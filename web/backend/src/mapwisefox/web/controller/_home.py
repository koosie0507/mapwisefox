import shutil
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, APIRouter, Request, UploadFile, File, Depends
from fastapi.responses import RedirectResponse

from ..config import AppSettings
from ..model import UserInfo
from ..view import templates

from ._deps import current_user, user_upload_dir, settings

router = APIRouter()


class UploadsController:
    def __init__(self, upload_dir: Path):
        self._upload_dir = upload_dir

    def list_files(self):
        files = list(self._upload_dir.glob("*.xlsx"))
        return files

    def save(self, filename, content):
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        path = self._upload_dir / filename
        with path.open("wb") as f:
            shutil.copyfileobj(content, f)
        return path

    def delete(self, filename):
        path = self._upload_dir / filename
        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        path.unlink()


@lru_cache()
def create_controller(upload_dir: Path):
    return UploadsController(upload_dir)


def uploads_controller(
    dir_path: Path = Depends(user_upload_dir),
) -> UploadsController | None:
    return create_controller(dir_path)


@router.get("/", name="home")
def home(
    request: Request,
    config: AppSettings = Depends(settings),
    user: UserInfo = Depends(current_user),
    controller: UploadsController = Depends(uploads_controller),
):
    files = controller.list_files()
    return templates.TemplateResponse(
        "home.j2",
        {
            "request": request,
            "files": files,
            "user": user,
            "auth_enabled": config.auth_enabled,
        },
    )


@router.post("/upload", name="upload_file")
async def upload_file(
    file: UploadFile = File(...),
    controller: UploadsController = Depends(uploads_controller),
):
    controller.save(file.filename, file.file)
    return RedirectResponse("/", status_code=303)


@router.post("/delete/{filename}", name="delete_file")
async def delete_file(
    filename: str,
    controller: UploadsController = Depends(uploads_controller),
):
    controller.delete(filename)
    return RedirectResponse("/", status_code=303)
