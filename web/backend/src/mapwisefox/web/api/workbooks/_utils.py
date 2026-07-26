import json
from pathlib import Path

from fastapi import HTTPException
from pydantic import ValidationError

from mapwisefox.common.config import SelectionConfig
from mapwisefox.web.model import (
    WorkbookRepository,
    WorkbookValidationError,
    workbook_path,
)

from ._models import EvidenceResponse, ScreeningResponse
from ._cache import _undecided_indexes


def _parse_field_mappings(value: str | None) -> dict[str, str]:
    if value is None or not value.strip():
        return {}
    try:
        mappings = json.loads(value)
    except json.JSONDecodeError as error:
        raise WorkbookValidationError(
            "invalid_field_mappings", f"Invalid JSON: {error}"
        ) from error
    if not isinstance(mappings, dict) or not all(
        isinstance(field, str) and isinstance(column, str)
        for field, column in mappings.items()
    ):
        raise WorkbookValidationError(
            "invalid_field_mappings", "Field mappings must be an object of strings"
        )
    if any(
        not field.strip() or not column.strip() for field, column in mappings.items()
    ):
        raise WorkbookValidationError(
            "invalid_field_mappings", "Field mappings must not contain blank names"
        )
    return {field.strip(): column.strip() for field, column in mappings.items()}


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


def _validate_selection_criteria(content: bytes) -> SelectionConfig | None:
    try:
        payload = json.loads(content)
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
