from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PIL import Image
import pytest

from mapwisefox.assistant.tools.pdf._layout_extractor import PdfLayoutExtractor


def _element(kind, coordinates):
    return SimpleNamespace(type=kind, block=SimpleNamespace(coordinates=coordinates))


class _Pool:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def submit(self, function, image):
        future = Future()
        future.set_result(function(image=image))
        return future


def test_layout_extractor_public_call_reports_missing_poppler(tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)

    with pytest.raises(RuntimeError, match="Poppler"):
        PdfLayoutExtractor()(tmp_path / "paper.pdf")


def test_layout_extractor_public_call_writes_debug_image(tmp_path):
    image = Image.new("RGB", (100, 200))
    model = MagicMock()
    model.detect.return_value = [_element("Text", (0, 0, 10, 10))]
    extractor = PdfLayoutExtractor(debug=True)

    with (
        patch("shutil.which", return_value="/usr/bin/pdftoppm"),
        patch(
            "mapwisefox.assistant.tools.pdf._layout_extractor.AutoLayoutModel",
            return_value=model,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._layout_extractor.ThreadPoolExecutor",
            return_value=_Pool(),
        ),
        patch("pdf2image.convert_from_path", return_value=[image]),
    ):
        result = extractor(tmp_path / "paper.pdf")

    assert result == (tmp_path / "paper.pdf").resolve()
    assert extractor.image_sizes[0].width == 100
    assert extractor.page_layouts[0][0].types == ["Text"]
    assert (tmp_path / "debug_paper" / "page_0000.png").exists()


def test_layout_extractor_public_call_merges_overlapping_detected_boxes(tmp_path):
    image = Image.new("RGB", (100, 200))
    model = MagicMock()
    model.detect.return_value = [
        _element("Text", (0, 0, 10, 10)),
        _element("Title", (1, 1, 9, 9)),
    ]
    extractor = PdfLayoutExtractor()

    with (
        patch("shutil.which", return_value="/usr/bin/pdftoppm"),
        patch(
            "mapwisefox.assistant.tools.pdf._layout_extractor.AutoLayoutModel",
            return_value=model,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._layout_extractor.ThreadPoolExecutor",
            return_value=_Pool(),
        ),
        patch("pdf2image.convert_from_path", return_value=[image]),
    ):
        extractor(tmp_path / "paper.pdf")

    assert len(extractor.page_layouts[0]) == 1
