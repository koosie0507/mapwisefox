from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING, get_args

from mapwisefox.web.model import Evidence

if TYPE_CHECKING:
    from mapwisefox.web.model import WorkbookRepository


_NON_IMPORTED_FIELDS = frozenset({"cluster_id", "include", "exclude_reasons"})
_SUPPORTED_FIELD_NAMES = {
    field.alias or name: name
    for name, field in Evidence.model_fields.items()
    if name not in _NON_IMPORTED_FIELDS
}


def _is_mandatory(field) -> bool:
    return field.is_required() and type(None) not in get_args(field.annotation)


SUPPORTED_FIELDS = dict(
    sorted(
        (
            (alias, _is_mandatory(Evidence.model_fields[name]))
            for alias, name in _SUPPORTED_FIELD_NAMES.items()
        ),
        key=lambda item: not item[1],
    )
)

_WORKBOOK_UNDECIDED: dict[Path, list[int]] = {}


def _mapped_column(field: str, field_mappings: dict[str, str]) -> str:
    return field_mappings.get(field, _SUPPORTED_FIELD_NAMES[field])


def _evidence_field(field: str) -> str:
    return _SUPPORTED_FIELD_NAMES[field]


def _mapped_columns(field_mappings: dict[str, str]) -> set[str]:
    return {_mapped_column(field, field_mappings) for field in SUPPORTED_FIELDS}


def _mapped_value(
    values: dict[str, Any], field: str, field_mappings: dict[str, str]
) -> Any:
    return values.get(_mapped_column(field, field_mappings))


def _validate_field_mappings(
    headers: list[str], field_mappings: dict[str, str]
) -> None:
    missing = [
        field
        for field, mandatory in SUPPORTED_FIELDS.items()
        if mandatory and _mapped_column(field, field_mappings) not in headers
    ]
    if missing:
        from mapwisefox.web.model import WorkbookValidationError

        raise WorkbookValidationError(
            "missing_mandatory_fields",
            f"Missing mandatory fields: {', '.join(missing)}",
        )


def _undecided_indexes(repository: WorkbookRepository) -> list[int]:
    path = repository.path.resolve()
    if path not in _WORKBOOK_UNDECIDED:
        _WORKBOOK_UNDECIDED[path] = repository.undecided_indexes()
    return _WORKBOOK_UNDECIDED[path]


def _remove_undecided_index(repository: WorkbookRepository, record_index: int) -> None:
    cached_undecided = _undecided_indexes(repository)
    if record_index in cached_undecided:
        cached_undecided.remove(record_index)


def _clear_undecided_cache_entry(
    entry: WorkbookRepository | Path,
) -> list[int] | None:
    path = entry.path if hasattr(entry, "path") else entry
    if not isinstance(path, Path):
        raise TypeError()
    return _WORKBOOK_UNDECIDED.pop(path.resolve(), None)
