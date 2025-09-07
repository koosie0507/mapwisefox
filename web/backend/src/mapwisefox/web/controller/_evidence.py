from pathlib import Path

from fastapi import APIRouter, Request, Depends, Body
from mapwisefox.web.model import Evidence
from numpy import clip

from ._deps import user_upload_dir, current_user, settings
from ._evidence_viewmodel import ToggleEvidenceStatusRequestBody, EvidenceViewModel, NavigateRequestBody, \
    NavigateResponseBody, ToggleEvidenceStatusResponseBody
from ..config import AppSettings
from ..utils import any_to_bool, KeyedInstanceCache, resolve_frontend_info
from ..model import UserInfo, PandasRepo, NavigateAction
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
        return self._repo.navigate(self._current_id, "unfilled")

    @property
    def first_non_specified(self):
        return self._repo.navigate(0, "unfilled")

    @property
    def first_id(self):
        return self._repo.navigate(self._current_id, "first")

    @property
    def last_id(self):
        return self._repo.navigate(self._current_id, "last")

    @property
    def next_id(self):
        return self._repo.navigate(self._current_id, "next")

    @property
    def prev_id(self):
        return self._repo.navigate(self._current_id, "prev")

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

    @property
    def all_filled(self) -> bool:
        return not self._repo.has_unfilled

    def navigate(self, cluster_id: int, action: NavigateAction) -> Evidence:
        desired_id = self._repo.navigate(cluster_id, action)
        self.selected_index = desired_id
        return self.current_record

    def update(self, cluster_id: int, include: str):
        evidence = self._repo.get(cluster_id)
        evidence.include = any_to_bool(include)
        self._repo.update(evidence)

    def save_current_record(self):
        try:
            self._repo.update(self.current_record)
        except ValueError:
            return

    @staticmethod
    def __sanitize_exclude_reason(exclude_reason: str) -> str:
        if exclude_reason is None or not isinstance(exclude_reason, str):
            return ""
        return exclude_reason.strip().lower()

    def toggle_status(self, cluster_id: int, include: bool, exclude_reasons: list[str]):
        evidence = self._repo.get(cluster_id)

        # remove duplicates, sanitize, update include status
        changed = evidence.include != include
        evidence.include = include

        new_exclude_reasons = {
            reason: None
            for r in exclude_reasons
            if (reason:=self.__sanitize_exclude_reason(r))
        }
        if len(new_exclude_reasons) > 1 and self.UNSPECIFIED_REASON in new_exclude_reasons:
            del new_exclude_reasons[self.UNSPECIFIED_REASON]
        evidence.exclude_reasons = list(new_exclude_reasons)
        changed &= len(evidence.exclude_reasons) == len(exclude_reasons)

        self._repo.update(evidence)
        return changed


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
        index if index is not None else controller.first_non_specified
    )
    all_done = False
    if controller.selected_index < 0:
        all_done = True
        controller.selected_index = controller.first_id
    frontend_ok, res_or_info = resolve_frontend_info(config, "src/main.ts")
    if not frontend_ok:
        return res_or_info

    viewmodel = EvidenceViewModel(controller.current_record)
    json_record = viewmodel.model_dump(by_alias=True)
    return templates.TemplateResponse(
        "form.j2",
        {
            "debug": config.debug,
            "dev_server_url": config.dev_server_url,
            "request": request,
            "user": user,
            "auth_enabled": config.auth_enabled,
            "all_done": all_done,
            "record": json_record,
            "filename": controller.filename,
            "index": controller.selected_index,
            "count": controller.count,
            # frontend
            "script_src": res_or_info.script_source,
            "css_hrefs": res_or_info.css_hrefs,
            "widget_name": "EvidenceEditor"
        },
    )


@router.post("/{filename}/navigate", name="navigate")
def navigate(
    data: NavigateRequestBody = Body(),
    controller: EvidenceController = Depends(get_evidence_controller)
) -> NavigateResponseBody:
    evidence = controller.navigate(data.cluster_id, data.action)

    return NavigateResponseBody(
        evidence=EvidenceViewModel(evidence),
        minId=controller.first_id,
        maxId=controller.last_id
    )


@router.patch("/{filename}/save", name="save_status")
def toggle_status(
    toggle_data: ToggleEvidenceStatusRequestBody = Body(),
    controller: EvidenceController = Depends(get_evidence_controller),
) -> ToggleEvidenceStatusResponseBody:
    controller.selected_index = toggle_data.cluster_id
    changed = controller.toggle_status(
        toggle_data.cluster_id, toggle_data.include, toggle_data.exclude_reasons
    )
    current_record_vm = EvidenceViewModel(controller.current_record)
    return ToggleEvidenceStatusResponseBody(
        changed=changed,
        evidence=EvidenceViewModel(current_record_vm),
        complete=controller.all_filled,
    )
