from pathlib import Path

from mapwisefox.web.model import WorkbookRepository

_WORKBOOK_UNDECIDED: dict[Path, list[int]] = {}


def _undecided_indexes(repository: WorkbookRepository) -> list[int]:
    path = repository.path.resolve()
    if path not in _WORKBOOK_UNDECIDED:
        _WORKBOOK_UNDECIDED[path] = repository.undecided_indexes()
    return _WORKBOOK_UNDECIDED[path]


def _remove_undecided_index(repository: WorkbookRepository, record_index: int) -> None:
    cached_undecided = _undecided_indexes(repository)
    if record_index in cached_undecided:
        cached_undecided.remove(record_index)


def _clear_undecided_cache_entry(entry: WorkbookRepository | Path) -> list[int] | None:
    match entry:
        case WorkbookRepository():
            return _WORKBOOK_UNDECIDED.pop(entry.path.resolve(), None)
        case Path():
            return _WORKBOOK_UNDECIDED.pop(entry.resolve(), None)
        case _:
            raise TypeError()
