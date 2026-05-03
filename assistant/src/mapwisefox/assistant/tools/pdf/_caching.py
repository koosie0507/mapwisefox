from pathlib import Path

from mapwisefox.assistant.tools.pdf import FileContentsExtractor


class CachingFileContentsExtractor(FileContentsExtractor):
    def __init__(self, cache_dir: Path, extractor: FileContentsExtractor) -> None:
        self.__cache_dir = Path(cache_dir).resolve()
        self.__extractor = extractor

    def read_file(self, file: str | Path) -> str:
        cached_file_path = self.__cache_dir / f"{file.stem}.txt"
        if cached_file_path.exists():
            return cached_file_path.read_text()

        text = self.__extractor.read_file(file)
        self.__cache_dir.mkdir(parents=True, exist_ok=True)
        cached_file_path.write_text(text)
        return text
