from unittest.mock import MagicMock, patch

from mapwisefox.assistant.tools.pdf._text_extractor import PdfTextExtractor
from mapwisefox.assistant.tools.pdf._types import Size


def _extract(path, visitor_text_args):
    page = MagicMock()
    page.mediabox = [0, 0, 100, 200]

    def extract_text(visitor_text):
        for args in visitor_text_args:
            visitor_text(*args)

    page.extract_text.side_effect = extract_text
    reader = MagicMock(pages=[page])
    reader.__enter__.return_value = reader
    reader.__exit__.return_value = False

    with patch(
        "mapwisefox.assistant.tools.pdf._text_extractor.PdfReader", return_value=reader
    ):
        extractor = PdfTextExtractor()
        result = extractor(path)
    return extractor, result


def test_text_extractor_public_call_keeps_body_text_and_filters_noise(tmp_path):
    path = tmp_path / "paper.pdf"
    path.write_bytes(b"pdf")
    visitor_args = [
        ("body text", [1, 0, 0, 1, 0, 0], [1, 0, 0, 1, 10, 100], None, 10),
        ("the and", [1, 0, 0, 1, 0, 0], [1, 0, 0, 1, 10, 100], None, 10),
        ("---", [1, 0, 0, 1, 0, 0], [1, 0, 0, 1, 10, 100], None, 10),
        ("header", [1, 0, 0, 1, 0, 0], [1, 0, 0, 1, 10, 195], None, 10),
    ]

    extractor, result = _extract(path, visitor_args)

    assert result == path.resolve()
    assert extractor.page_sizes[0] == Size(100, 200)
    assert [item.text for item in extractor.text_items[0]] == ["body text"]


def test_text_extractor_public_call_uses_font_metrics(tmp_path):
    path = tmp_path / "paper.pdf"
    path.write_bytes(b"pdf")
    font = {"/FontBBox": [0, -200, 1000, 800], "/Widths": [500], "/FirstChar": 65}
    args = [("AB", [1, 0, 0, 1, 0, 0], [1, 0, 0, 1, 10, 100], font, 10)]

    extractor, _ = _extract(path, args)

    assert extractor.text_items[0][0].font_size == 10
    assert extractor.text_items[0][0].bounds.size.width == 10
