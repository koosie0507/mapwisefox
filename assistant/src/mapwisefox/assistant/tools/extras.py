from importlib import import_module
from types import ModuleType


def try_import(name: str, extra: str = None) -> ModuleType:
    try:
        return import_module(name)
    except ModuleNotFoundError as e:
        if e.name == name:
            msg = (
                f"The required module {name!r} is not installed. Specify the {extra!r} extra."
                if extra
                else f"The required module {name!r} is not installed."
            )
            raise ImportError(msg)
        raise
