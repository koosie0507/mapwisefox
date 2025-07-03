import json
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, Request

from mapwisefox.web._settings import AppSettings
from mapwisefox.web.model import UserInfo


@lru_cache()
def settings() -> AppSettings:
    return AppSettings()


def app_basedir(config: AppSettings = Depends(settings)) -> Path:
    return config.basedir


def current_user(request: Request) -> UserInfo | None:
    if request.session is None or "user" not in request.session:
        return None
    current_session_user = json.loads(request.session["user"])
    return UserInfo(**current_session_user)


def user_upload_dir(
    config: AppSettings = Depends(settings),
    user_info: UserInfo | None = Depends(current_user),
) -> Path | None:
    if user_info is None:
        return config.uploads_dir
    return config.uploads_dir / user_info.dirname
