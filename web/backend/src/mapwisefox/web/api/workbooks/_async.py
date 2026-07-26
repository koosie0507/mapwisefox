import asyncio
from pathlib import Path

_WORKBOOK_LOCKS: dict[Path, asyncio.Lock] = {}


def _lock_for(path: Path) -> asyncio.Lock:
    return _WORKBOOK_LOCKS.setdefault(path.resolve(), asyncio.Lock())
