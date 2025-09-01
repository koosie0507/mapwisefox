from typing import Any


__STR_TRUE = {"yes", "y", "true", "t", "on", "1", "include"}
__STR_FALSE = {"no", "n", "false", "f", "off", "0", "exclude", ""}


def any_to_bool(value: Any) -> bool:
    if value is None:
        return False

    str_val = str(value).strip().lower()
    if str_val in __STR_TRUE:
        return True
    if str_val in __STR_FALSE:
        return False

    raise ValueError(f"can't convert '{value}' to bool")
