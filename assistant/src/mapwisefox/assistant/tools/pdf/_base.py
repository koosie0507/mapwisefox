from abc import ABC, abstractmethod
from enum import StrEnum
from pathlib import Path


class FileContentsExtractor(ABC):
    @abstractmethod
    def read_file(self, file: str | Path) -> str:
        pass


class ExtractionFailureReason(StrEnum):
    Generic = "uncaught error"
    Timeout = "timed out"
    BackendError = "backend processing failure"


class FileContentsExtractionError(Exception):
    def __init__(
        self,
        reason: ExtractionFailureReason,
        file_path: str | Path | None = None,
        additional_information: str = "",
    ):
        desc = self.__get_description(additional_information, file_path, reason)
        super().__init__(desc)
        self.reason = reason
        self.file_path = file_path
        self.description = desc

    @classmethod
    def __get_description(
        cls,
        additional_information: str,
        file_path: str | Path | None,
        reason: ExtractionFailureReason,
    ):
        fpath = file_path or "<unknown>"
        return (
            f"{reason}({fpath}): {additional_information}"
            if additional_information
            else f"failed to extract contents of {fpath}: {reason}"
        )
