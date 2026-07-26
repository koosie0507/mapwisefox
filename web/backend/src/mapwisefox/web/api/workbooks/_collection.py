import asyncio
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from mapwisefox.web.config import AppSettings
from mapwisefox.web.model import (
    WorkbookMetadata,
    WorkbookRepository,
    WorkbookValidationError,
    workbook_path,
)

from ..._deps import settings, user_upload_dir
from ._async import _lock_for
from ._cache import _clear_undecided_cache_entry
from ._utils import (
    _metadata,
    _parse_field_mappings,
    _raise_http,
    _validate_selection_criteria,
)

router = APIRouter()


@router.get(
    "/workbooks", response_model=list[WorkbookMetadata], response_model_by_alias=True
)
async def list_workbooks(upload_dir: Path = Depends(user_upload_dir)):
    def load_metadata() -> list[WorkbookMetadata]:
        if not upload_dir.is_dir():
            return []
        metadata = []
        for path in sorted(upload_dir.glob("*.xlsx")):
            try:
                metadata.append(_metadata(WorkbookRepository(path)))
            except FileNotFoundError:
                continue
        return metadata

    return await asyncio.to_thread(load_metadata)


@router.post(
    "/workbooks",
    response_model=WorkbookMetadata,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def import_workbook(
    response: Response,
    file: UploadFile = File(...),
    worksheet_name: str | None = Form(None, alias="worksheetName"),
    field_mappings: str | None = Form(None, alias="fieldMappings"),
    decision_column: str | None = Form(None, alias="decisionColumn"),
    exclusion_reason_column: str | None = Form(None, alias="exclusionReasonColumn"),
    selection_criteria_file: UploadFile | None = File(None, alias="selectionCriteria"),
    upload_dir: Path = Depends(user_upload_dir),
    config: AppSettings = Depends(settings),
):
    temporary_path: Path | None = None
    try:
        name = file.filename or ""
        destination = workbook_path(upload_dir, name)
        worksheet = (
            worksheet_name.strip()
            if worksheet_name and worksheet_name.strip()
            else None
        )
        mappings = _parse_field_mappings(field_mappings)
        decision = decision_column or config.decision_column
        exclusion = exclusion_reason_column or config.exclusion_reason_column
        selection_criteria_file_content = (
            await selection_criteria_file.read()
            if selection_criteria_file is not None
            else None
        )
        selection_criteria = (
            _validate_selection_criteria(selection_criteria_file_content)
            if selection_criteria_file_content
            else None
        )
        upload_dir.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(dir=upload_dir, suffix=".xlsx")
        with os.fdopen(descriptor, "wb") as stream:
            await asyncio.to_thread(shutil.copyfileobj, file.file, stream)
        temporary_path = Path(temporary_name)
        async with _lock_for(destination):
            imported = await asyncio.to_thread(
                WorkbookRepository.import_workbook,
                temporary_path,
                destination,
                worksheet,
                mappings,
                decision,
                exclusion,
                selection_criteria,
            )
            _clear_undecided_cache_entry(destination)
            metadata = await asyncio.to_thread(
                _metadata, WorkbookRepository(destination, imported)
            )
        response.headers["Location"] = f"/api/v1/workbooks/{name}"
        return metadata
    except (WorkbookValidationError, FileNotFoundError) as error:
        _raise_http(error)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        await file.close()
        if selection_criteria_file is not None:
            await selection_criteria_file.close()
