from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from mapwisefox.web.config import settings, STATIC_ROUTE
from mapwisefox.web.controller import (
    evidence_router,
    main_router,
    auth_router,
)
from mapwisefox.web.utils import MultiStaticFiles


def _init_app():
    app_settings = settings()
    app = FastAPI(title="ERSA SMS - Primary Study Selection")
    app.add_middleware(SessionMiddleware, secret_key="secret")
    staticfile_dirs = [app_settings.static_files_dir]
    if not app_settings.debug:
        staticfile_dirs.append(app_settings.static_files_dir / "dist" / "assets")
    app.mount(STATIC_ROUTE, MultiStaticFiles(staticfile_dirs), name="assets")
    app.include_router(evidence_router)
    app.include_router(auth_router)
    app.include_router(main_router)

    return app
