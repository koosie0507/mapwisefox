import time
from functools import wraps
from typing import Callable, Concatenate, Optional


LoggerCallback = Callable[Concatenate[str, ...], None]


def timer(callback: LoggerCallback, label: Optional[str] = None):
    label = label or "operation"

    def wrapper(f):
        @wraps(f)
        def _(*args, **kwargs):
            start_time = time.time_ns()
            callback("%s: starting", label)
            try:
                return f(*args, **kwargs)
            finally:
                end_time = time.time_ns()
                milliseconds = (end_time - start_time) // 1000000
                callback("%s: finished in %d ms", label, milliseconds)

        return _

    return wrapper
