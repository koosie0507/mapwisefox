from unittest.mock import MagicMock, patch

import pytest

from mapwisefox.assistant.tools.pdf._base import (
    ExtractionFailureReason,
    FileContentsExtractionError,
)
from mapwisefox.assistant.tools.pdf._docling import ConversionError, DoclingExtractor


def _extractor(artifacts_path=None, error_callback=None):
    options = MagicMock()
    with (
        patch(
            "mapwisefox.assistant.tools.pdf._docling.PdfPipelineOptions",
            return_value=options,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._docling.PdfFormatOption",
            return_value=MagicMock(),
        ),
    ):
        return DoclingExtractor(artifacts_path, error_callback=error_callback)


class _Process:
    def __init__(self, target, args):
        self.target = target
        self.args = args
        self.exitcode = 0

    def start(self):
        pass

    def join(self):
        pass

    def terminate(self):
        self.exitcode = -1


class _RunningProcess(_Process):
    def start(self):
        try:
            self.target(*self.args)
        except Exception:
            self.exitcode = 1


def test_docling_extractor_downloads_artifacts_when_path_is_supplied(tmp_path):
    with patch("mapwisefox.assistant.tools.pdf._docling.download_models") as download:
        _extractor(tmp_path / "artifacts")

    download.assert_called_once()


def test_docling_extractor_public_read_returns_markdown(tmp_path):
    extractor = _extractor()
    recv = MagicMock()
    recv.poll.return_value = True
    recv.recv.return_value = "markdown"
    process = _Process

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._docling.Pipe",
            return_value=(recv, MagicMock()),
        ),
        patch("mapwisefox.assistant.tools.pdf._docling.Process", process),
    ):
        assert extractor.read_file(tmp_path / "paper.pdf") == "markdown"


def test_docling_extractor_public_read_unloads_backend_after_conversion(tmp_path):
    converter = MagicMock()
    backend = MagicMock()
    converter.convert.return_value.input._backend = backend
    converter.convert.return_value.document.export_to_markdown.return_value = "markdown"
    extractor = _extractor()
    recv = MagicMock()
    recv.poll.return_value = True
    recv.recv.return_value = "markdown"

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._docling.DocumentConverter",
            return_value=converter,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._docling.Pipe",
            return_value=(recv, MagicMock()),
        ),
        patch("mapwisefox.assistant.tools.pdf._docling.Process", _RunningProcess),
    ):
        assert extractor.read_file(tmp_path / "paper.pdf") == "markdown"

    backend.unload.assert_called_once()


def test_docling_extractor_public_read_reports_conversion_failure(tmp_path):
    callback = MagicMock()
    converter = MagicMock()
    converter.convert.side_effect = ConversionError("conversion failed")
    extractor = _extractor(error_callback=callback)
    recv = MagicMock()
    recv.poll.return_value = True
    recv.recv.return_value = "conversion error"

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._docling.DocumentConverter",
            return_value=converter,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._docling.Pipe",
            return_value=(recv, MagicMock()),
        ),
        patch("mapwisefox.assistant.tools.pdf._docling.Process", _RunningProcess),
        pytest.raises(FileContentsExtractionError) as raised,
    ):
        extractor.read_file(tmp_path / "paper.pdf")

    assert raised.value.reason == ExtractionFailureReason.BackendError
    callback.assert_called_once()


def test_docling_extractor_public_read_reports_generic_conversion_failure(tmp_path):
    converter = MagicMock()
    converter.convert.side_effect = RuntimeError("conversion failed")
    extractor = _extractor()
    recv = MagicMock()
    recv.poll.return_value = True
    recv.recv.return_value = "unhandled error"

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._docling.DocumentConverter",
            return_value=converter,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._docling.Pipe",
            return_value=(recv, MagicMock()),
        ),
        patch("mapwisefox.assistant.tools.pdf._docling.Process", _RunningProcess),
        pytest.raises(FileContentsExtractionError),
    ):
        extractor.read_file(tmp_path / "paper.pdf")


def test_docling_extractor_public_read_raises_timeout(tmp_path):
    extractor = _extractor()
    recv = MagicMock()
    recv.poll.return_value = False

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._docling.Pipe",
            return_value=(recv, MagicMock()),
        ),
        patch("mapwisefox.assistant.tools.pdf._docling.Process", _Process),
        pytest.raises(FileContentsExtractionError) as raised,
    ):
        extractor.read_file(tmp_path / "paper.pdf")

    assert raised.value.reason == ExtractionFailureReason.Timeout


def test_docling_extractor_public_read_wraps_process_setup_errors(tmp_path):
    extractor = _extractor()

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._docling.Pipe",
            side_effect=RuntimeError("pipe failed"),
        ),
        pytest.raises(FileContentsExtractionError) as raised,
    ):
        extractor.read_file(tmp_path / "paper.pdf")

    assert raised.value.reason == ExtractionFailureReason.Generic
