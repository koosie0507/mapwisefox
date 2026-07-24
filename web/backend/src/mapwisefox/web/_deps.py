from pathlib import Path

from authlib.jose.errors import JoseError
from fastapi import Depends, HTTPException, Request

from mapwisefox.web.config import settings, AppSettings
from mapwisefox.web.model import UserInfo


def current_user(
    request: Request, config: AppSettings = Depends(settings)
) -> UserInfo | None:
    if not config.auth_enabled:
        return None
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if not token:
        return None
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    try:
        return request.app.state.tokens.validate_access_token(token)
    except JoseError as error:
        raise HTTPException(status_code=401, detail="Invalid access token") from error


def user_upload_dir(
    config: AppSettings = Depends(settings),
    user_info: UserInfo | None = Depends(current_user),
) -> Path:
    if config.auth_enabled and user_info is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user_info is None:
        return config.uploads_dir
    return config.uploads_dir / user_info.dirname
