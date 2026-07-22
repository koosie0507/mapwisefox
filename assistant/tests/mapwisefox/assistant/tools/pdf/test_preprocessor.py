from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mapwisefox.assistant.tools.pdf._preprocessor import ensure_page_dimensions


def _box(width, height):
    return SimpleNamespace(width=width, height=height)


def test_ensure_page_dimensions_uses_cropbox_when_dimensions_are_valid(tmp_path):
    path = tmp_path / "paper.pdf"
    path.write_bytes(b"original")
    cropbox = _box(10, 20)
    page = SimpleNamespace(cropbox=cropbox, mediabox=_box(30, 40))
    reader = MagicMock(pages=[page])
    writer = MagicMock()

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._preprocessor.PdfReader",
            return_value=reader,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._preprocessor.PdfWriter",
            return_value=writer,
        ),
    ):
        ensure_page_dimensions(path)

    assert page.mediabox is cropbox
    assert page.cropbox is cropbox
    writer.add_page.assert_called_once_with(page)
    writer.write.assert_called_once()
    reader.close.assert_called_once()
    writer.close.assert_called_once()


def test_ensure_page_dimensions_falls_back_to_mediabox(tmp_path):
    path = tmp_path / "paper.pdf"
    path.write_bytes(b"original")
    mediabox = _box(30, 40)
    page = SimpleNamespace(cropbox=_box(0, 0), mediabox=mediabox)
    reader = MagicMock(pages=[page])
    writer = MagicMock()

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._preprocessor.PdfReader",
            return_value=reader,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._preprocessor.PdfWriter",
            return_value=writer,
        ),
    ):
        ensure_page_dimensions(path)

    assert page.cropbox is mediabox


def test_ensure_page_dimensions_restores_original_file_on_failure(tmp_path):
    path = tmp_path / "paper.pdf"
    original = b"original"
    path.write_bytes(original)
    page = SimpleNamespace(cropbox=_box(10, 20), mediabox=_box(30, 40))
    reader = MagicMock(pages=[page])
    writer = MagicMock()
    writer.write.side_effect = RuntimeError("cannot write")

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._preprocessor.PdfReader",
            return_value=reader,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._preprocessor.PdfWriter",
            return_value=writer,
        ),
        pytest.raises(RuntimeError, match="cannot write"),
    ):
        ensure_page_dimensions(path)

    assert path.read_bytes() == original
