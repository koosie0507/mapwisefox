from abc import ABC, abstractmethod
from pathlib import Path


class FileContentsExtractor(ABC):
    @abstractmethod
    def read_file(self, file: str | Path) -> str:
        pass
