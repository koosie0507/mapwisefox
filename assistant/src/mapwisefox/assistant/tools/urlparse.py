from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import url2pathname


class UrlInfo:
    def __init__(self, uri: str) -> None:
        self.__uri = uri
        self.__parts = urlsplit(uri)

    @property
    def local_path(self) -> Path:
        if self.__parts.scheme != "file" or self.__parts.netloc not in {
            "",
            "localhost",
        }:
            raise ValueError(f"URI {self.__uri!r} does not describe a local file")
        return Path(url2pathname(self.__parts.path)).resolve()

    @property
    def scheme(self) -> str:
        return self.__parts.scheme
