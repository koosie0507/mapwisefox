from http import HTTPStatus
from pathlib import Path

import numpy as np
import pandas as pd
from cachetools import TTLCache
from fastapi import APIRouter, Request, Form, Depends, Body
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from numpy import clip
from starlette.responses import JSONResponse

from ._deps import user_upload_dir, current_user, settings
from ._evidence_viewmodel import ReasonToggle, EvidenceViewModel
from .._settings import AppSettings
from ..utils import any_to_bool, KeyedInstanceCache
from ..model import UserInfo, PandasRepo
from ..view import templates

router = APIRouter(prefix="/evidence", dependencies=[Depends(user_upload_dir)])


class EvidenceController(metaclass=KeyedInstanceCache):
    UNSPECIFIED_REASON = "<unspecified reason>"
    DEFAULT_ALIASES = {
        "exclude_reason": "exclude_reasons",
        "source": "publication_venue",
        "year": "publication_date",
        "referencing_paper_ids": "referencing_evidence"
    }

    def __init__(self, excel_file: Path):
        self._excel_file = Path(excel_file)
        self._repo = PandasRepo(excel_file, aliases=self.DEFAULT_ALIASES)
        self._current_id = -1

    def __hash__(self):
        return hash(self._excel_file)

    def __eq__(self, other):
        return self._excel_file == other._excel_file

    @property
    def next_non_specified(self):
        if "include" not in self._repo.dataframe.columns:
            return -1
        include = self._repo.dataframe["include"]
        mask = (include.isnull()) | (include.isna()) | (include == "")
        start_id = np.argmax(mask.to_numpy()) if mask.any() else -1
        return start_id

    @staticmethod
    def __safe_int(value):
        if pd.isna(value):
            return -1
        return int(value)

    @property
    def first_id(self):
        return self.__safe_int(self._repo.dataframe.index.min())

    @property
    def last_id(self):
        return self.__safe_int(self._repo.dataframe.index.max())

    @property
    def next_id(self):
        return self.__safe_int(self._repo.dataframe[self._repo.dataframe.index > self._current_id].index.min() or -1)

    @property
    def prev_id(self):
        return self.__safe_int(self._repo.dataframe[self._repo.dataframe.index < self._current_id].index.max() or -1)

    @property
    def count(self):
        return self._repo.dataframe.shape[0]

    def all(self):
        return self._repo.dataframe.to_dict(orient="records")

    @property
    def filename(self):
        return self._excel_file.name

    @property
    def selected_index(self):
        return self._current_id

    @selected_index.setter
    def selected_index(self, value):
        self._current_id = clip(value, self.first_id, self.last_id)

    @property
    def current_record(self):
        if self.selected_index == -1:
            raise ValueError("selected index explicitly deactivated current record")
        return self._repo.get(self.selected_index)

    def update(self, cluster_id: int, include: str):
        evidence = self._repo.get(cluster_id)
        evidence.include = any_to_bool(include)
        self._repo.update(evidence)

    def save_current_record(self):
        try:
            self._repo.update(self.current_record)
        except ValueError:
            return

    def update_exclude_reason(self, cluster_id: int, exclude: bool, reason: str):
        evidence = self._repo.get(cluster_id)
        exclude_reasons = {
            reason.strip(): None for reason in evidence.exclude_reasons if reason
        }
        if self.UNSPECIFIED_REASON in exclude_reasons:
            del exclude_reasons[self.UNSPECIFIED_REASON]
        before_len = len(exclude_reasons)

        # add or remove exclude reason based on toggle
        if exclude:
            exclude_reasons[reason] = None
        else:
            if reason in exclude_reasons:
                del exclude_reasons[reason]
        after_len = len(exclude_reasons)
        evidence.exclude_reasons = list(exclude_reasons)

        # update the include/exclude flag
        evidence.include = after_len <= 0
        self._repo.update(evidence)

        # the number of reasons changed
        return after_len != before_len


def get_evidence_controller(
        filename: str, upload_dir=Depends(user_upload_dir)
) -> EvidenceController:
    return EvidenceController(upload_dir / filename)


@router.get("/{filename}", name="show_evidence")
def show_form(
        request: Request,
        index: int | None = None,
        config: AppSettings = Depends(settings),
        user: UserInfo = Depends(current_user),
        controller: EvidenceController = Depends(get_evidence_controller),
):
    controller.selected_index = (
        index if index is not None else controller.next_non_specified
    )
    all_done = False
    if controller.selected_index < 0:
        all_done = True
        controller.selected_index = controller.first_id

    viewmodel = EvidenceViewModel(controller.current_record)
    return templates.TemplateResponse(
        "form.j2",
        {
            "request": request,
            "user": user,
            "auth_enabled": config.auth_enabled,
            "all_done": all_done,
            "record": viewmodel,
            "filename": controller.filename,
            "index": controller.selected_index,
            "count": controller.count,
        },
    )


@router.post("/{filename}/process-form", name="edit_evidence")
def handle_navigation(
        filename: str,
        action: str = Form(...),
        index: int = Form(0),
        controller: EvidenceController = Depends(get_evidence_controller),
):
    if controller is None:
        return RedirectResponse("/", status_code=303)

    basepath = f"/evidence/{filename}"
    if action == "next-unfilled":
        return RedirectResponse(basepath, status_code=303)
    if action == "goto":
        return RedirectResponse(f"{basepath}?index={index - 1}", status_code=303)
    # Navigation logic
    controller.save_current_record()
    next_index = controller.selected_index
    if action == "next" and next_index < controller.last_id:
        next_index = controller.next_id
    elif action == "prev" and next_index > controller.first_id:
        next_index = controller.prev_id
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    url = f"{basepath}?index={next_index}" if next_index is not None else basepath
    return RedirectResponse(url, status_code=303)


@router.patch("/{filename}/toggle-exclude-reason", name="toggle_exclude_reason")
def handle_toggle_include(
        toggle_data: ReasonToggle = Body(...),
        controller: EvidenceController = Depends(get_evidence_controller),
):
    changed = controller.update_exclude_reason(
        toggle_data.id, toggle_data.toggle, toggle_data.exclude_reason
    )
    current_record_vm = EvidenceViewModel(controller.current_record)
    return JSONResponse(
        {
            "id": toggle_data.id,
            "saved": changed,
            "selection_status": current_record_vm.selection_status,
            "remaining_exclusions": current_record_vm.exclude_reasons,
        },
        status_code=HTTPStatus.ACCEPTED,
    )
