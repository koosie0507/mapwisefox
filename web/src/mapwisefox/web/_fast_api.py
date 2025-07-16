from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from mapwisefox.web.controller import (
    evidence_router,
    main_router,
    auth_router,
)
from mapwisefox.web.static import static_dir_path

APP_BASE_DIR = Path(__file__).resolve().parent


def _init_app():
    app = FastAPI(title="ERSA SMS - Primary Study Selection")
    app.add_middleware(SessionMiddleware, secret_key="secret")
    app.mount("/static", StaticFiles(directory=static_dir_path), name="static")
    app.include_router(evidence_router)
    app.include_router(auth_router)
    app.include_router(main_router)

    return app
