from fastapi import APIRouter, Depends, Request

from mapwisefox.web.config import AppSettings
from mapwisefox.web.model import UserInfo
from mapwisefox.web.view import templates

from .._deps import current_user, settings, user_upload_dir


router = APIRouter()


@router.get("/", name="home", dependencies=[Depends(user_upload_dir)])
def home(
    request: Request,
    config: AppSettings = Depends(settings),
    user: UserInfo | None = Depends(current_user),
):
    return templates.TemplateResponse(
        "home.j2",
        {
            "request": request,
            "user": user,
            "auth_enabled": config.auth_enabled,
            "worksheet_name": config.worksheet_name or "",
            "expected_columns": config.expected_columns or "",
            "decision_column": config.decision_column,
            "exclusion_reason_column": config.exclusion_reason_column,
        },
    )
