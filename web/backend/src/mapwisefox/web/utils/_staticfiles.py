from os import PathLike

from starlette.staticfiles import StaticFiles
from starlette.responses import Response


class MultiStaticFiles:
    def __init__(self, directories: list[PathLike]):
        self.apps = [StaticFiles(directory=d) for d in directories]

    async def __call__(self, scope, receive, send):
        for app in self.apps:
            try:
                return await app(scope, receive, send)
            except Exception:
                continue
        return Response("Not Found", status_code=404)
