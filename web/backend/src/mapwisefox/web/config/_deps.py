from functools import lru_cache

from ._settings import AppSettings


@lru_cache()
def settings() -> AppSettings:
    return AppSettings()
