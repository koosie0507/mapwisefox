import json
from pathlib import Path

from pydantic.dataclasses import dataclass
from starlette.responses import HTMLResponse, Response

from mapwisefox.web.config import AppSettings, STATIC_ROUTE


def _resolve_manifest_path(static_dir):
    return static_dir / "dist" / ".vite" / "manifest.json"


def _manifest_lookup(static_dir: Path, entry: str) -> str | None:
    """Return built asset path for a given source entry using Vite manifest."""
    manifest_path = _resolve_manifest_path(static_dir)
    if not manifest_path.exists():
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    item = manifest.get(entry)
    if not item:
        return None
    item_file = item["file"]
    return f"{STATIC_ROUTE}/dist/{item_file}"


@dataclass(frozen=True)
class FrontendInfo:
    script_source: str
    css_hrefs: list[str]


def resolve_frontend_info(
    settings: AppSettings, entry: str
) -> tuple[bool, FrontendInfo | Response]:
    if settings.debug:
        script_src = f"{settings.dev_server_url}/src/main.ts"
        css_hrefs: list[str] = []  # Vite injects styles in dev
    else:
        built_js = _manifest_lookup(settings.static_files_dir, entry)
        if not built_js:
            # Helpful error for first-timers who forgot to build
            return False, HTMLResponse(
                content=(
                    "<h1>Build missing</h1>"
                    "<p>Run <code>npm run build</code> inside <code>frontend/</code> "
                    f"to generate <code>{_resolve_manifest_path(settings.static_files_dir)}</code>.</p>"
                ),
                status_code=500,
            )
        script_src = built_js
        css_hrefs = []
        try:
            with open(
                _resolve_manifest_path(settings.static_files_dir), "r", encoding="utf-8"
            ) as f:
                manifest = json.load(f)
            if manifest.get(entry, {}).get("css"):
                css_hrefs = [f"/{STATIC_ROUTE}/{p}" for p in manifest[entry]["css"]]
        except Exception:
            css_hrefs = []

    return True, FrontendInfo(script_src, css_hrefs)
