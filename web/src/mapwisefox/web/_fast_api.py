from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from mapwisefox.web.config import settings, STATIC_ROUTE
from mapwisefox.web.controller import (
    evidence_router,
    main_router,
    auth_router,
)


def _init_app():
    app_settings = settings()
    app = FastAPI(title="ERSA SMS - Primary Study Selection")
    app.add_middleware(SessionMiddleware, secret_key="secret")
    app.mount(STATIC_ROUTE, StaticFiles(directory=app_settings.static_files_dir), name="static")
    if not app_settings.debug:
        app.mount(
            "/assets",
            StaticFiles(directory=app_settings.static_files_dir / "dist" / "assets"),
            name="assets"
        )
    app.include_router(evidence_router)
    app.include_router(auth_router)
    app.include_router(main_router)

    return app
