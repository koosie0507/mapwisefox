from unittest.mock import MagicMock, patch

from mapwisefox.assistant.tools.pdf._pdf import BasicPdfMarkdownExtractor
from mapwisefox.assistant.tools.pdf._types import LayoutBox, Point, Rect, Size, TextItem


def _item(text, bounds):
    return TextItem(text, 10, None, bounds)


def _box(kind, bounds):
    return LayoutBox([kind], bounds)


def _extractor(text_items, layout_boxes):
    text_extractor = MagicMock()
    text_extractor.page_sizes = {0: Size(100, 100)}
    text_extractor.text_items = {0: text_items}
    layout_extractor = MagicMock()
    layout_extractor.image_sizes = {0: Size(100, 100)}
    layout_extractor.page_layouts = {0: layout_boxes}

    return text_extractor, layout_extractor


def test_basic_pdf_markdown_extractor_public_read_combines_layout_text(tmp_path):
    bounds = Rect(Point(0, 0), Point(100, 20))
    text_extractor, layout_extractor = _extractor(
        [_item("Heading", bounds), _item("body", bounds)],
        [_box("Title", bounds)],
    )

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._pdf.PdfTextExtractor",
            return_value=text_extractor,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._pdf.PdfLayoutExtractor",
            return_value=layout_extractor,
        ),
    ):
        result = BasicPdfMarkdownExtractor().read_file(tmp_path / "paper.pdf")

    assert "## Heading\nbody" in result


def test_basic_pdf_markdown_extractor_public_read_handles_hyphenated_text(tmp_path):
    bounds = Rect(Point(0, 0), Point(100, 20))
    text_extractor, layout_extractor = _extractor(
        [_item("hyphen-", bounds), _item("ated", bounds)],
        [_box("Text", bounds)],
    )

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._pdf.PdfTextExtractor",
            return_value=text_extractor,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._pdf.PdfLayoutExtractor",
            return_value=layout_extractor,
        ),
    ):
        result = BasicPdfMarkdownExtractor().read_file(tmp_path / "paper.pdf")

    assert result == "hyphenated"


def test_basic_pdf_markdown_extractor_public_read_skips_non_overlapping_text(
    tmp_path,
):
    text_bounds = Rect(Point(20, 20), Point(30, 30))
    box_bounds = Rect(Point(0, 0), Point(10, 10))
    text_extractor, layout_extractor = _extractor(
        [_item("outside", text_bounds)], [_box("Text", box_bounds)]
    )

    with (
        patch(
            "mapwisefox.assistant.tools.pdf._pdf.PdfTextExtractor",
            return_value=text_extractor,
        ),
        patch(
            "mapwisefox.assistant.tools.pdf._pdf.PdfLayoutExtractor",
            return_value=layout_extractor,
        ),
    ):
        result = BasicPdfMarkdownExtractor().read_file(tmp_path / "paper.pdf")

    assert result == ""
