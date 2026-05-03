import inspect
import threading
from pathlib import Path

import cachetools
from fastapi import HTTPException


class KeyedInstanceCache(type):
    __CACHE_LOCK = threading.RLock()
    __CACHE = cachetools.TTLCache(maxsize=12, ttl=600)
    __KEYS = {"path", "excel_path", "excel_file"}
    __DEFAULT_KEY = "<default>"

    @classmethod
    def __fetch_first_key(cls, kwargs, keys):
        try:
            return next(v for k, v in kwargs.items() if k in keys)
        except StopIteration:
            return None

    def __call__(cls, *args, **kwargs):
        sig = inspect.signature(cls.__init__)
        bound = sig.bind_partial(None, *args, **kwargs)  # placeholder for self
        bound.apply_defaults()
        args_map = dict(bound.arguments)
        args_map.pop("self", None)
        cache_key = cls.__fetch_first_key(args_map, cls.__KEYS) or cls.__DEFAULT_KEY

        with cls.__CACHE_LOCK:
            path = Path(cache_key)
            if cache_key != cls.__DEFAULT_KEY and (
                not path.exists() or not path.is_file()
            ):
                raise HTTPException(status_code=404, detail="File not found")

            if cache_key not in cls.__CACHE:
                cls.__CACHE[cache_key] = super().__call__(*args, **kwargs)
            return cls.__CACHE[cache_key]
