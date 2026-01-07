import hashlib
import os
import re
from pathlib import Path
from urllib.request import url2pathname

import requests

from mapwisefox.assistant.tools.urlparse import UrlInfo


class FileProvider:
    __FILENAME_RE = re.compile(r"filename=(.+)\b")

    def __init__(
        self, cache_dir: Path, chunk_size: int = 16384, timeout: int = 60
    ) -> None:
        if cache_dir.exists() and not cache_dir.is_dir():
            raise ValueError(f"{cache_dir} exists and is not a directory")
        self.__cache_dir = Path(cache_dir).resolve()
        self.__session = requests.Session()
        self.__cookie_jar = {}
        self.__chunk_size = chunk_size
        self.__timeout = timeout

    @staticmethod
    def __local_filename(download_url: str) -> str:
        name = url2pathname(download_url.split("/")[-1])
        if name.endswith(".pdf"):
            name = name[:-4]
        md5 = hashlib.md5(download_url.encode()).hexdigest()
        return f"{name}-{md5}.pdf"

    def __download(self, url: str) -> Path:
        local_filename = self.__local_filename(url)
        file_path = self.__cache_dir / local_filename
        file_hash_path = self.__cache_dir / f"{local_filename}.sha256"

        should_download = True
        if file_path.exists() and file_hash_path.exists():
            with open(file_hash_path) as precomputed_hash:
                hash1 = precomputed_hash.readline()
            with open(file_path, "rb") as pdf:
                hash2 = hashlib.sha256(pdf.read()).hexdigest()
            should_download = hash1 != hash2
        if not should_download:
            return file_path

        with self.__session.get(
            url,
            verify=False,
            cookies=self.__cookie_jar,
            timeout=self.__timeout,
            stream=True,
        ) as res:
            res.raise_for_status()
            content_type = res.headers["Content-Type"]
            if "pdf" not in content_type:
                raise ValueError(f"can't handle content type {content_type!r}")

            self.__cache_dir.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb+") as pdf:
                for chunk in res.iter_content(chunk_size=self.__chunk_size):
                    pdf.write(chunk)
                pdf.seek(0, os.SEEK_SET)
                new_hash = hashlib.sha256(pdf.read())
            with open(file_hash_path, "w") as f:
                f.write(new_hash.hexdigest())

        return file_path

    def __call__(self, url: str) -> Path:
        info = UrlInfo(url)
        if info.scheme in {"http", "https"}:
            return self.__download(url)
        elif info.scheme == "file":
            return info.local_path
        else:
            raise ValueError(f"URL scheme {info.scheme!r} is not supported")
