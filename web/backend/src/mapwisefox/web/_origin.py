from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from mapwisefox.web.config import AppSettings


COOKIE_AUTH_PATHS = {"/auth/refresh", "/auth/logout"}


class OriginGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, config: AppSettings) -> None:
        super().__init__(app)
        self._config = config
        public = urlsplit(config.public_url or "")
        self._origins = config.configured_origins | {
            f"{public.scheme}://{public.netloc}".rstrip("/")
        }

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("Origin")
        requires_origin = (
            request.method == "POST" and request.url.path in COOKIE_AUTH_PATHS
        )
        if requires_origin and not origin:
            return JSONResponse({"detail": "Origin required"}, status_code=403)
        if origin and not self._allowed(origin):
            return JSONResponse({"detail": "Origin not allowed"}, status_code=403)
        return await call_next(request)

    def _allowed(self, origin: str) -> bool:
        parsed = urlsplit(origin)
        return origin.rstrip("/") in self._origins or parsed.hostname in {
            "localhost",
            "127.0.0.1",
        }
