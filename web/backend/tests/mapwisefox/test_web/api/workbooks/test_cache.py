from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mapwisefox.web.api.workbooks._cache import (
    _clear_undecided_cache_entry,
    _remove_undecided_index,
    _undecided_indexes,
    _WORKBOOK_UNDECIDED,
)
from mapwisefox.web.model import WorkbookRepository


def test_undecided_indexes_populates_cache():
    repository = MagicMock(spec=WorkbookRepository)
    path = Path("/tmp/workbook.xlsx")
    repository.path = path
    repository.undecided_indexes.return_value = [1, 3]

    assert _undecided_indexes(repository) == [1, 3]
    assert path.resolve() in _WORKBOOK_UNDECIDED


def test_undecided_indexes_reuses_cached_value():
    repository = MagicMock(spec=WorkbookRepository)
    path = Path("/tmp/cached.xlsx")
    repository.path = path
    repository.undecided_indexes.return_value = [1]

    _undecided_indexes(repository)
    repository.undecided_indexes.return_value = [2]

    assert _undecided_indexes(repository) == [1]
    repository.undecided_indexes.assert_called_once()


def test_remove_undecided_index_removes_existing_record():
    repository = MagicMock(spec=WorkbookRepository)
    path = Path("/tmp/remove.xlsx")
    repository.path = path
    repository.undecided_indexes.return_value = [0, 1]

    _remove_undecided_index(repository, 0)

    assert _WORKBOOK_UNDECIDED[path.resolve()] == [1]


def test_remove_undecided_index_is_noop_for_unknown_record():
    repository = MagicMock(spec=WorkbookRepository)
    path = Path("/tmp/noop.xlsx")
    repository.path = path
    repository.undecided_indexes.return_value = [1]

    _remove_undecided_index(repository, 0)

    assert _WORKBOOK_UNDECIDED[path.resolve()] == [1]


def test_clear_undecided_cache_entry_for_repository():
    repository = MagicMock(spec=WorkbookRepository)
    path = Path("/tmp/repo.xlsx")
    repository.path = path
    repository.undecided_indexes.return_value = [0]

    _undecided_indexes(repository)
    removed = _clear_undecided_cache_entry(repository)

    assert removed == [0]
    assert path.resolve() not in _WORKBOOK_UNDECIDED


def test_clear_undecided_cache_entry_for_path():
    repository = MagicMock()
    path = Path("/tmp/by_path.xlsx")
    repository.path = path
    repository.undecided_indexes.return_value = [0]

    _undecided_indexes(repository)
    removed = _clear_undecided_cache_entry(path)

    assert removed == [0]
    assert path.resolve() not in _WORKBOOK_UNDECIDED


def test_clear_undecided_cache_entry_for_unknown_path_returns_none():
    path = Path("/tmp/unknown.xlsx")

    assert _clear_undecided_cache_entry(path) is None


def test_clear_undecided_cache_entry_rejects_invalid_entry_type():
    with pytest.raises(TypeError):
        _clear_undecided_cache_entry("not a repository or path")
