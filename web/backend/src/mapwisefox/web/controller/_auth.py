from urllib.parse import urlsplit

from authlib.integrations.base_client import OAuthError
from authlib.jose.errors import JoseError
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from mapwisefox.web._auth import (
    OIDC_STATE_LIFETIME,
    REFRESH_TOKEN_LIFETIME,
    OidcService,
    TokenService,
)
from mapwisefox.web.config import AppSettings


REFRESH_COOKIE = "mwf_refresh"
STATE_COOKIE = "mwf_oidc_state"

router = APIRouter(prefix="/auth", tags=["authentication"])


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


def _auth_services(request: Request) -> tuple[AppSettings, OidcService, TokenService]:
    config = request.app.state.config
    if not config.auth_enabled:
        raise HTTPException(status_code=404)
    return config, request.app.state.oidc, request.app.state.tokens


def _allowed_return_url(config: AppSettings, return_to: str) -> str:
    target = urlsplit(return_to)
    if target.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Invalid return URL")
    origin = f"{target.scheme}://{target.netloc}".rstrip("/")
    public_origin = _origin(config.public_url or "")
    if origin in config.configured_origins | {public_origin} or _is_local(
        target.hostname
    ):
        return return_to
    raise HTTPException(status_code=400, detail="Invalid return URL")


def _origin(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _is_local(hostname: str | None) -> bool:
    return hostname in {"localhost", "127.0.0.1"}


def _secure_cookie(config: AppSettings) -> bool:
    return urlsplit(config.public_url or "").scheme == "https"


@router.get("/login")
async def login(request: Request, return_to: str | None = None):
    config, oidc, _ = _auth_services(request)
    destination = _allowed_return_url(config, return_to or config.public_url or "")
    response, state = await oidc.begin_login(request, destination)
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=OIDC_STATE_LIFETIME,
        secure=_secure_cookie(config),
        httponly=True,
        samesite="lax",
        path="/auth/callback",
    )
    return response


@router.get("/callback")
async def callback(request: Request):
    config, oidc, tokens = _auth_services(request)
    if request.cookies.get(STATE_COOKIE) != request.query_params.get("state"):
        raise HTTPException(status_code=400, detail="Invalid authentication state")
    try:
        user, return_to = await oidc.complete_login(request)
    except (OAuthError, JoseError, KeyError, ValueError) as error:
        raise HTTPException(status_code=400, detail="Authentication failed") from error
    response = RedirectResponse(return_to, status_code=303)
    response.delete_cookie(STATE_COOKIE, path="/auth/callback")
    response.set_cookie(
        REFRESH_COOKIE,
        tokens.issue_refresh_token(user),
        max_age=REFRESH_TOKEN_LIFETIME,
        secure=_secure_cookie(config),
        httponly=True,
        samesite="lax",
        path="/auth",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(request: Request, response: Response):
    _, _, tokens = _auth_services(request)
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        user = tokens.validate_refresh_token(refresh_token)
    except JoseError as error:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from error
    response.headers["Cache-Control"] = "no-store"
    return AccessTokenResponse(access_token=tokens.issue_access_token(user))


@router.post("/logout", status_code=204)
def logout(request: Request):
    config, _, _ = _auth_services(request)
    response = Response(status_code=204)
    response.delete_cookie(
        REFRESH_COOKIE,
        secure=_secure_cookie(config),
        httponly=True,
        samesite="lax",
        path="/auth",
    )
    response.headers["Cache-Control"] = "no-store"
    return response
