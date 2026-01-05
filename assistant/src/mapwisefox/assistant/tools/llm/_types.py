from typing import Callable


type ErrorCallback = Callable[[str, Exception], None]
type TextCallback = Callable[[str], None]
