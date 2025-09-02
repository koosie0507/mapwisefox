from threading import RLock

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import RedirectResponse

from mapwisefox.web.config import AppSettings
from mapwisefox.web.model import UserInfo
from mapwisefox.web.controller._deps import settings


router = APIRouter(prefix="/auth")


class OAuthSingleton:
    __lock = RLock()

    def __new__(cls, *args, **kwargs):
        with cls.__lock:
            if not hasattr(cls, "__instance"):
                setattr(cls, "__instance", super().__new__(cls))
            return getattr(cls, "__instance")

    def __init__(self, config: AppSettings) -> None:
        self.__oauth = self.__register_oauth(config)

    @property
    def oauth(self) -> OAuth:
        return self.__oauth

    @staticmethod
    def __register_oauth(config: AppSettings) -> OAuth:
        result = OAuth()
        result.register(
            name="microsoft",
            client_id=config.ms_client_id,
            client_secret=config.ms_client_secret,
            access_token_url=f"https://login.microsoftonline.com/{config.ms_tenant_id}/oauth2/v2.0/token",
            authorize_url=f"https://login.microsoftonline.com/{config.ms_tenant_id}/oauth2/v2.0/authorize",
            api_base_url="https://graph.microsoft.com/v1.0/",
            client_kwargs={
                "scope": "User.Read",
            },
        )
        return result


def get_oauth(config: AppSettings = Depends(settings)) -> OAuth:
    return OAuthSingleton(config).oauth


@router.post("/login", name="login")
async def login(request: Request, oauth: OAuth = Depends(get_oauth)):
    redirect_uri = request.url_for("auth")
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth(request: Request, oauth: OAuth = Depends(get_oauth)):
    token = await oauth.microsoft.authorize_access_token(request)
    user = await oauth.microsoft.get("me", token=token)
    user_data = user.json()
    user_obj = UserInfo(
        dirname=user_data["displayName"].lower().replace(" ", "-"),
        display_name=user_data["displayName"],
        email=user_data["mail"],
        given_name=user_data["givenName"],
        surname=user_data["surname"],
    )
    request.session["user"] = user_obj.model_dump_json()
    return RedirectResponse(url="/")


@router.post("/logout")
async def logout(request: Request):
    del request.session["user"]
    return RedirectResponse(url="/", status_code=303)


@router.get("/sso-logout")
async def sso_logout(request: Request):
    del request.session["user"]
    return Response(status_code=204)
