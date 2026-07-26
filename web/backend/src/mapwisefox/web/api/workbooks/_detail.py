import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, status

from mapwisefox.web.model import WorkbookMetadata

from ..._deps import user_upload_dir
from ._async import _lock_for
from ._cache import _remove_undecided_index, _clear_undecided_cache_entry
from ._models import ScreeningPatch, ScreeningResponse
from ._utils import _metadata, _raise_http, _repository, _response

router = APIRouter()


@router.get(
    "/workbooks/{name}", response_model=WorkbookMetadata, response_model_by_alias=True
)
async def get_workbook(name: str, upload_dir: Path = Depends(user_upload_dir)):
    return _metadata(_repository(upload_dir, name))


@router.delete("/workbooks/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workbook(name: str, upload_dir: Path = Depends(user_upload_dir)):
    repository = _repository(upload_dir, name)
    async with _lock_for(repository.path):
        try:
            await asyncio.to_thread(repository.delete)
        except FileNotFoundError as error:
            _raise_http(error)
        _clear_undecided_cache_entry(repository)


@router.get(
    "/workbooks/{name}/screening/{record_index}",
    response_model=ScreeningResponse,
    response_model_by_alias=True,
)
async def get_screening_record(
    name: str,
    record_index: int,
    upload_dir: Path = Depends(user_upload_dir),
):
    repository = _repository(upload_dir, name)
    try:
        return await asyncio.to_thread(_response, repository, record_index)
    except IndexError as error:
        _raise_http(error)


@router.patch(
    "/workbooks/{name}/screening/{record_index}",
    response_model=ScreeningResponse,
    response_model_by_alias=True,
)
async def update_screening_record(
    name: str,
    record_index: int,
    patch: ScreeningPatch,
    upload_dir: Path = Depends(user_upload_dir),
):
    repository = _repository(upload_dir, name)
    reasons = []
    if patch.decision == "excluded":
        reasons = list(
            dict.fromkeys(
                reason.strip().lower()
                for reason in patch.exclusion_reasons
                if reason.strip()
            )
        )
    async with _lock_for(repository.path):
        try:
            await asyncio.to_thread(
                repository.update, record_index, patch.decision, reasons
            )
            _remove_undecided_index(repository, record_index)
            return await asyncio.to_thread(_response, repository, record_index)
        except IndexError as error:
            _raise_http(error)
