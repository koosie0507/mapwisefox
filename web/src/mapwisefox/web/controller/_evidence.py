from http import HTTPStatus
from pathlib import Path
from threading import RLock
from urllib.parse import urlencode

import numpy as np
import pandas as pd
from cachetools import TTLCache
from fastapi import APIRouter, Request, Form, Depends, Body
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from numpy import clip
from pydantic import BaseModel
from starlette.responses import JSONResponse

from ._deps import user_upload_dir, current_user, settings
from .._settings import AppSettings
from ..model import UserInfo
from ..view import templates

router = APIRouter(prefix="/evidence", dependencies=[Depends(user_upload_dir)])
cache_lock = RLock()
controller_cache = TTLCache(maxsize=12, ttl=600)


class EvidenceController:
    UNSPECIFIED_REASON = "<unspecified reason>"

    def __init__(self, excel_file: Path):
        self._excel_file = Path(excel_file)
        self._df = pd.read_excel(excel_file).sort_index(axis=1, inplace=False)
        self._df["include"] = self._df["include"].astype(str).replace("nan", None)
        if "exclude_reason" not in self._df.columns:
            self._df["exclude_reason"] = self._df["include"].case_when(
                [
                    (self._df["include"] == "include", ""),
                    (self._df["include"] == "exclude", self.UNSPECIFIED_REASON),
                    (self._df["include"].isna(), None),
                ]
            )
        self._df.set_index("cluster_id", inplace=True)
        self._current_index = -1

    def __hash__(self):
        return hash(self._excel_file)

    def __eq__(self, other):
        return self._excel_file == other._excel_file

    @property
    def next_non_specified(self):
        include = self._df["include"]
        mask = (include.isnull()) | (include.isna()) | (include == "")
        start_idx = np.argmax(mask.to_numpy()) if mask.any() else -1
        return start_idx

    @property
    def count(self):
        return self._df.shape[0]

    def all(self):
        return self._df.to_dict(orient="records")

    @property
    def filename(self):
        return self._excel_file.name

    @property
    def selected_index(self):
        return self._current_index

    @selected_index.setter
    def selected_index(self, value):
        self._current_index = clip(value, 0, self.count - 1)

    @property
    def current_record(self):
        if self.selected_index == -1:
            raise ValueError("selected index explicitly deactivated current record")
        row_index = self._df.index[self._current_index]
        row = self._df.loc[[row_index]].reset_index().squeeze()
        return row

    def update(self, cluster_id: int, include: str):
        self._df.at[cluster_id, "include"] = include
        self._df.to_excel(self._excel_file)

    def update_exclude_reason(self, cluster_id: int, exclude: bool, reason: str):
        reason = reason.lower().strip()
        exclude_reasons = self._df.at[cluster_id, "exclude_reason"] or ""
        # retain unique values preserving order
        exclude_reasons = {
            reason.strip(): None for reason in exclude_reasons.split(",") if reason
        }

        # remove placeholder from importing files saved with a previous version of the app
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
        self._df.at[cluster_id, "exclude_reason"] = ", ".join(exclude_reasons)

        # update the include/exclude flag
        self._df.at[cluster_id, "include"] = "exclude" if after_len > 0 else "include"
        self._df.to_excel(self._excel_file)

        # the number of reasons changed
        return after_len != before_len


def create_controller(path: Path) -> EvidenceController:
    with cache_lock:
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        if path not in controller_cache:
            controller_cache[path] = EvidenceController(path)
        controller_cache[path] = controller_cache[path]
        return controller_cache[path]


def get_evidence_controller(
    filename: str, upload_dir=Depends(user_upload_dir)
) -> EvidenceController:
    return create_controller(upload_dir / filename)


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
        controller.selected_index = 0

    current_record_obj = controller.current_record.fillna("").to_dict()
    current_record_obj["exclude_reason"] = current_record_obj["exclude_reason"] or ""
    current_record_obj["exclude_reason"] = current_record_obj["exclude_reason"].split(
        ", "
    )
    current_record_obj["url"] = current_record_obj["url"] or (
        "https://www.semanticscholar.org/search?{}".format(
            urlencode({
                "q": current_record_obj["title"],
            })
        )
    )
    return templates.TemplateResponse(
        "form.j2",
        {
            "request": request,
            "user": user,
            "auth_enabled": config.auth_enabled,
            "all_done": all_done,
            "record": current_record_obj,
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
    next_index = controller.selected_index
    if action == "next" and next_index < controller.count - 1:
        next_index = next_index + 1
    elif action == "prev" and next_index > 0:
        next_index = next_index - 1
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    url = f"{basepath}?index={next_index}" if next_index is not None else basepath
    return RedirectResponse(url, status_code=303)


class ReasonToggle(BaseModel):
    id: int
    toggle: bool
    exclude_reason: str


@router.patch("/{filename}/toggle-exclude-reason", name="toggle_exclude_reason")
def handle_toggle_include(
    toggle_data: ReasonToggle = Body(...),
    controller: EvidenceController = Depends(get_evidence_controller),
):
    changed = controller.update_exclude_reason(
        toggle_data.id, toggle_data.toggle, toggle_data.exclude_reason
    )
    selection_status = str(controller.current_record["include"])
    remaining_exclude_reasons = [
        reason
        for reason in controller.current_record["exclude_reason"].split(", ")
        if reason
    ]
    return JSONResponse(
        {
            "id": toggle_data.id,
            "saved": changed,
            "selection_status": selection_status,
            "remaining_exclusions": remaining_exclude_reasons,
        },
        status_code=HTTPStatus.ACCEPTED,
    )
