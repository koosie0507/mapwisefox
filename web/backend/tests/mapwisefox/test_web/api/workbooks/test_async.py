import asyncio
from pathlib import Path

from mapwisefox.web.api.workbooks._async import _lock_for


def test_lock_for_returns_lock_for_path():
    lock = _lock_for(Path("/tmp/workbook.xlsx"))
    assert isinstance(lock, asyncio.Lock)


def test_lock_for_returns_same_lock_for_same_path():
    path = Path("/tmp/unique.xlsx")
    assert _lock_for(path) is _lock_for(path)


def test_lock_for_returns_different_locks_for_different_paths():
    assert _lock_for(Path("/tmp/a.xlsx")) is not _lock_for(Path("/tmp/b.xlsx"))


def test_lock_for_resolves_paths_before_lookup():
    assert _lock_for(Path("/tmp/../tmp/workbook.xlsx")) is _lock_for(
        Path("/tmp/workbook.xlsx")
    )
