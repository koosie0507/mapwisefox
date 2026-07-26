import csv
import json
from pathlib import Path

from fastapi import HTTPException, UploadFile
from pydantic import ValidationError

from mapwisefox.common.config import SelectionConfig
from mapwisefox.web.model import (
    WorkbookRepository,
    WorkbookValidationError,
    workbook_path,
)

from ._models import EvidenceResponse, ScreeningResponse
from ._cache import _undecided_indexes


def _parse_expected_columns(value: str) -> list[str]:
    try:
        rows = list(csv.reader([value], strict=True))
    except csv.Error as error:
        raise WorkbookValidationError(
            "invalid_expected_columns", f"Invalid CSV: {error}"
        ) from error
    columns = [column.strip() for column in rows[0]] if rows else []
    if not columns or any(not column for column in columns):
        raise WorkbookValidationError(
            "invalid_expected_columns", "Expected columns must be non-empty"
        )
    duplicates = sorted({column for column in columns if columns.count(column) > 1})
    if duplicates:
        raise WorkbookValidationError(
            "duplicate_expected_columns",
            f"Duplicate expected columns: {', '.join(duplicates)}",
        )
    return columns


def _resolved(value: str | None, fallback: str | None, field: str) -> str:
    result = value.strip() if value and value.strip() else fallback
    if not result:
        raise WorkbookValidationError(
            "missing_import_configuration", f"Missing import field: {field}"
        )
    return result


def _raise_http(error: Exception) -> None:
    if isinstance(error, WorkbookValidationError):
        raise HTTPException(status_code=422, detail=error.detail()) from error
    if isinstance(error, FileNotFoundError):
        raise HTTPException(status_code=404, detail="Workbook not found") from error
    if isinstance(error, IndexError):
        raise HTTPException(
            status_code=404, detail="Screening record not found"
        ) from error
    raise error


def _validate_selection_criteria(file: UploadFile) -> SelectionConfig | None:
    try:
        payload = json.loads(file.file.read())
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_selection_criteria", "message": str(error)},
        ) from error
    try:
        return SelectionConfig.model_validate(payload)
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_selection_criteria", "message": str(error)},
        ) from error


def _repository(upload_dir: Path, name: str) -> WorkbookRepository:
    try:
        return WorkbookRepository(workbook_path(upload_dir, name))
    except (WorkbookValidationError, FileNotFoundError) as error:
        _raise_http(error)
        assert False  # unreachable; used for typing conformity


def _metadata(repository: WorkbookRepository):
    return repository.metadata.model_copy(
        update={"unfilled_record_count": len(_undecided_indexes(repository))}
    )


def _response(repository: WorkbookRepository, record_index: int) -> ScreeningResponse:
    record = repository.get(record_index)
    undecided = _undecided_indexes(repository)
    next_undecided = next((index for index in undecided if index > record_index), None)
    return ScreeningResponse(
        recordIndex=record_index,
        recordCount=repository.metadata.record_count,
        decision=record.decision,
        exclusionReasons=record.exclusion_reasons,
        evidence=EvidenceResponse(record.evidence),
        previousIndex=record_index - 1 if record_index > 0 else None,
        nextIndex=(
            record_index + 1
            if record_index + 1 < repository.metadata.record_count
            else None
        ),
        firstUndecidedIndex=undecided[0] if undecided else None,
        nextUndecidedIndex=next_undecided,
        complete=not undecided,
        selectionCriteria=repository.metadata.selection_criteria,
    )
