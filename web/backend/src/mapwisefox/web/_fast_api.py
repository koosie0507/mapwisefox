from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mapwisefox.web._auth import OidcService, TokenService
from mapwisefox.web._origin import OriginGuardMiddleware
from mapwisefox.web.api import auth_api_router, config_api_router, workbooks_api_router
from mapwisefox.web.config import settings
from mapwisefox.web.hooks import auth_hooks


def _init_app():
    config = settings()
    app = FastAPI(title="ERSA SMS - Primary Study Selection")
    app.state.config = config
    if config.auth_enabled:
        app.state.tokens = TokenService(config.token_secret, config.public_url)
        app.state.oidc = OidcService(config)
        app.add_middleware(OriginGuardMiddleware, config=config)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(
                config.configured_origins | {config.public_url.rstrip("/")}
            ),
            allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )
    app.include_router(auth_api_router)
    app.include_router(config_api_router)
    app.include_router(workbooks_api_router)
    app.include_router(auth_hooks)

    return app
