from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from mapwisefox.web.api import config_api_router, workbooks_api_router
from mapwisefox.web.controller import auth_router


def _init_app():
    app = FastAPI(title="ERSA SMS - Primary Study Selection")
    app.add_middleware(SessionMiddleware, secret_key="secret")
    app.include_router(config_api_router)
    app.include_router(workbooks_api_router)
    app.include_router(auth_router)

    return app
