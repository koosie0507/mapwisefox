import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from mapwisefox.web.config import settings
from mapwisefox.web.controller import (
    evidence_router,
    main_router,
    auth_router,
)

STATIC_ROUTE = "/static"


def _manifest_lookup(static_dir: Path, entry: str) -> str | None:
    """Return built asset path for a given source entry using Vite manifest."""
    manifest_path = static_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    item = manifest.get(entry)
    if not item:
        return None
    return f"{STATIC_ROUTE}/{item["file"]}"


def _init_app():
    app_settings = settings()
    app = FastAPI(title="ERSA SMS - Primary Study Selection")
    app.add_middleware(SessionMiddleware, secret_key="secret")
    app.mount(STATIC_ROUTE, StaticFiles(directory=app_settings.static_files_dir), name="static")
    app.include_router(evidence_router)
    app.include_router(auth_router)
    app.include_router(main_router)

    return app
