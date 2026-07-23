import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from mapwisefox.web.config import AppSettings
from mapwisefox.web.model import (
    UserInfo,
    WorkbookRepository,
    WorkbookValidationError,
    workbook_path,
)
from mapwisefox.web.utils import resolve_frontend_info
from mapwisefox.web.view import templates

from .._deps import current_user, settings, user_upload_dir
from ._evidence_viewmodel import EvidenceViewModel


router = APIRouter(prefix="/evidence", dependencies=[Depends(user_upload_dir)])


@router.get("/{filename}", name="show_evidence")
async def show_form(
    request: Request,
    filename: str,
    index: int | None = None,
    config: AppSettings = Depends(settings),
    user: UserInfo | None = Depends(current_user),
    upload_dir: Path = Depends(user_upload_dir),
):
    try:
        repository = await asyncio.to_thread(
            WorkbookRepository, workbook_path(upload_dir, filename)
        )
        undecided = await asyncio.to_thread(repository.undecided_indexes)
        record_index = (
            index if index is not None else (undecided[0] if undecided else 0)
        )
        record = await asyncio.to_thread(repository.get, record_index)
    except WorkbookValidationError as error:
        raise HTTPException(status_code=422, detail=error.detail()) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Workbook not found") from error
    except IndexError as error:
        raise HTTPException(
            status_code=404, detail="Screening record not found"
        ) from error

    frontend_ok, res_or_info = resolve_frontend_info(config, "src/main.ts")
    if not frontend_ok:
        return res_or_info
    return templates.TemplateResponse(
        "form.j2",
        {
            "debug": config.debug,
            "dev_server_url": config.dev_server_url,
            "request": request,
            "user": user,
            "auth_enabled": config.auth_enabled,
            "all_done": not undecided,
            "record": EvidenceViewModel(record.evidence).model_dump(by_alias=True),
            "filename": repository.path.name,
            "index": record_index,
            "count": repository.metadata.record_count,
            "script_src": res_or_info.script_source,
            "css_hrefs": res_or_info.css_hrefs,
            "widget_name": "EvidenceEditor",
        },
    )
