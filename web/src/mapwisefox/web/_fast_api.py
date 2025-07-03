from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from mapwisefox.web.controller import (
    evidence_router,
    main_router,
    auth_router,
)

APP_BASE_DIR = Path(__file__).resolve().parent


app = FastAPI()


def _init_app():
    app = FastAPI(title="ERSA SMS - Primary Study Selection")
    app.add_middleware(SessionMiddleware, secret_key="secret")
    app.mount("/static", StaticFiles(directory=APP_BASE_DIR / "static"), name="static")
    app.include_router(evidence_router)
    app.include_router(auth_router)
    app.include_router(main_router)

    return app
