from pathlib import Path

import pytest

from mapwisefox.assistant.tools.pdf._base import (
    ExtractionFailureReason,
    FileContentsExtractionError,
    FileContentsExtractor,
)


def test_extraction_error_contains_reason_and_path():
    error = FileContentsExtractionError(
        ExtractionFailureReason.Timeout, Path("paper.pdf")
    )

    assert error.reason == ExtractionFailureReason.Timeout
    assert error.file_path == Path("paper.pdf")
    assert "paper.pdf" in str(error)


def test_extraction_error_includes_additional_information():
    error = FileContentsExtractionError(
        ExtractionFailureReason.Generic, additional_information="broken"
    )

    assert "broken" in error.description
    assert "<unknown>" in error.description


def test_file_contents_extractor_is_abstract():
    with pytest.raises(TypeError):
        FileContentsExtractor()
