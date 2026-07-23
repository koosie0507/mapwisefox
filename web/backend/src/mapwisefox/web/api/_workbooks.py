import asyncio
import csv
import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict, Field, model_validator

from mapwisefox.web.config import AppSettings
from mapwisefox.web.model import (
    Decision,
    WorkbookMetadata,
    WorkbookRepository,
    WorkbookValidationError,
    workbook_path,
)

from .._deps import settings, user_upload_dir
from ..controller._evidence_viewmodel import EvidenceViewModel


router = APIRouter(prefix="/api/v1", tags=["workbooks"])
_WORKBOOK_LOCKS: dict[Path, asyncio.Lock] = {}
_WORKBOOK_UNDECIDED: dict[Path, list[int]] = {}


class ScreeningPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    decision: Decision
    exclusion_reasons: list[str] = Field(default_factory=list, alias="exclusionReasons")

    @model_validator(mode="after")
    def validate_excluded(self):
        if self.decision == "excluded" and not any(
            reason.strip() for reason in self.exclusion_reasons
        ):
            raise ValueError("Excluded records require at least one exclusion reason")
        return self


class ScreeningResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    record_index: int = Field(alias="recordIndex")
    record_count: int = Field(alias="recordCount")
    decision: Decision
    exclusion_reasons: list[str] = Field(alias="exclusionReasons")
    evidence: EvidenceViewModel
    previous_index: int | None = Field(alias="previousIndex")
    next_index: int | None = Field(alias="nextIndex")
    first_undecided_index: int | None = Field(alias="firstUndecidedIndex")
    next_undecided_index: int | None = Field(alias="nextUndecidedIndex")
    complete: bool


def _lock_for(path: Path) -> asyncio.Lock:
    return _WORKBOOK_LOCKS.setdefault(path.resolve(), asyncio.Lock())


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


def _repository(upload_dir: Path, name: str) -> WorkbookRepository:
    try:
        return WorkbookRepository(workbook_path(upload_dir, name))
    except (WorkbookValidationError, FileNotFoundError) as error:
        _raise_http(error)
        assert False  # unreachable; used for typing conformity


@lru_cache
def _undecided_indexes(repository: WorkbookRepository) -> list[int]:
    return repository.undecided_indexes()


def _response(repository: WorkbookRepository, record_index: int) -> ScreeningResponse:
    record = repository.get(record_index)
    undecided = _undecided_indexes(repository)
    next_undecided = next((index for index in undecided if index > record_index), None)
    return ScreeningResponse(
        recordIndex=record_index,
        recordCount=repository.metadata.record_count,
        decision=record.decision,
        exclusionReasons=record.exclusion_reasons,
        evidence=EvidenceViewModel(record.evidence),
        previousIndex=record_index - 1 if record_index > 0 else None,
        nextIndex=(
            record_index + 1
            if record_index + 1 < repository.metadata.record_count
            else None
        ),
        firstUndecidedIndex=undecided[0] if undecided else None,
        nextUndecidedIndex=next_undecided,
        complete=not undecided,
    )


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
                metadata.append(WorkbookRepository.read_metadata(path))
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
    expected_columns: str | None = Form(None, alias="expectedColumns"),
    decision_column: str | None = Form(None, alias="decisionColumn"),
    exclusion_reason_column: str | None = Form(None, alias="exclusionReasonColumn"),
    upload_dir: Path = Depends(user_upload_dir),
    config: AppSettings = Depends(settings),
):
    temporary_path: Path | None = None
    try:
        name = file.filename or ""
        destination = workbook_path(upload_dir, name)
        worksheet = _resolved(worksheet_name, config.worksheet_name, "worksheetName")
        expected = _parse_expected_columns(
            _resolved(expected_columns, config.expected_columns, "expectedColumns")
        )
        decision = _resolved(decision_column, config.decision_column, "decisionColumn")
        exclusion = _resolved(
            exclusion_reason_column,
            config.exclusion_reason_column,
            "exclusionReasonColumn",
        )
        upload_dir.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(dir=upload_dir, suffix=".xlsx")
        with os.fdopen(descriptor, "wb") as stream:
            await asyncio.to_thread(shutil.copyfileobj, file.file, stream)
        temporary_path = Path(temporary_name)
        async with _lock_for(destination):
            metadata = await asyncio.to_thread(
                WorkbookRepository.import_workbook,
                temporary_path,
                destination,
                worksheet,
                expected,
                decision,
                exclusion,
            )
        response.headers["Location"] = f"/api/v1/workbooks/{name}"
        return metadata
    except (WorkbookValidationError, FileNotFoundError) as error:
        _raise_http(error)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        await file.close()


@router.get(
    "/workbooks/{name}", response_model=WorkbookMetadata, response_model_by_alias=True
)
async def get_workbook(name: str, upload_dir: Path = Depends(user_upload_dir)):
    return _repository(upload_dir, name).metadata


@router.delete("/workbooks/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workbook(name: str, upload_dir: Path = Depends(user_upload_dir)):
    repository = _repository(upload_dir, name)
    async with _lock_for(repository.path):
        try:
            await asyncio.to_thread(repository.delete)
        except FileNotFoundError as error:
            _raise_http(error)


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
            cached_undecided = _undecided_indexes(repository)
            if record_index in cached_undecided:
                cached_undecided.remove(record_index)
            return await asyncio.to_thread(_response, repository, record_index)
        except IndexError as error:
            _raise_http(error)
