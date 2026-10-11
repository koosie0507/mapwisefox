import csv
import os
import tempfile
from io import BytesIO
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

from mapwisefox.shared.input import DEFAULT_HEADER_ALIASES, load_csv, resolve_headers

from ._repo import WorkbookValidationError


_EVIDENCE_FIELD_ALIASES = {
    "year": "publicationDate",
    "source": "publicationVenue",
    "has_pdf": "hasPdf",
}


def _evidence_field(record_field: str) -> str:
    return _EVIDENCE_FIELD_ALIASES.get(record_field, record_field)


def _csv_rows(csv_content: bytes) -> list[list[str]]:
    try:
        grid = load_csv(BytesIO(csv_content), header=False)
    except pd.errors.EmptyDataError as error:
        raise WorkbookValidationError(
            "missing_header", "CSV contains no header row"
        ) from error
    except (ValueError, csv.Error) as error:
        raise WorkbookValidationError(
            "invalid_workbook", "Uploaded file could not be parsed as CSV"
        ) from error
    return [
        [cell if isinstance(cell, str) else "" for cell in row]
        for row in grid.values.tolist()
    ]


def _header_row(rows: list[list[str]]) -> list[str]:
    for row in rows:
        if any(cell.strip() for cell in row):
            return [cell.strip() for cell in row]
    return []


def _field_mappings(
    rows: list[list[str]], explicit_mappings: dict[str, str] | None
) -> dict[str, str]:
    if explicit_mappings:
        return explicit_mappings
    resolved = resolve_headers(_header_row(rows), DEFAULT_HEADER_ALIASES)
    return {
        _evidence_field(record_field): header
        for header, record_field in resolved.items()
    }


def _as_workbook(rows: list[list[str]]) -> Workbook:
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    return workbook


def convert_csv_to_workbook(
    csv_content: bytes,
    destination_dir: Path,
    explicit_mappings: dict[str, str] | None = None,
) -> tuple[Path, dict[str, str]]:
    """Convert CSV records into a temporary .xlsx workbook.

    Returns the workbook path together with the field mappings to use for the
    import: the explicit mappings when provided, otherwise mappings resolved
    from the CSV header row through the shared header alias registry.
    """
    rows = _csv_rows(csv_content)
    mappings = _field_mappings(rows, explicit_mappings)
    workbook = _as_workbook(rows)
    descriptor, temporary_name = tempfile.mkstemp(dir=destination_dir, suffix=".xlsx")
    os.close(descriptor)
    try:
        workbook.save(temporary_name)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    finally:
        workbook.close()
    return Path(temporary_name), mappings
