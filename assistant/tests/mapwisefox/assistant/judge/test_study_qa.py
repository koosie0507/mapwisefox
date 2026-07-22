from unittest.mock import MagicMock

from mapwisefox.assistant.config import ReaderType
from mapwisefox.assistant.judge import _study_qa as qa


def test_reader_factory_uses_custom_reader(monkeypatch):
    reader = object()
    monkeypatch.setattr(qa, "get_default_pdf_reader", lambda dpi, layout_model: reader)

    assert qa.reader_factory(ReaderType.custom, "layout") is reader


def test_reader_factory_uses_docling_reader(monkeypatch):
    reader = object()
    docling = MagicMock()
    docling.DoclingExtractor.return_value = reader
    monkeypatch.setattr(qa, "try_import", lambda name: docling)

    assert qa.reader_factory(ReaderType.docling, "layout") is reader
    docling.DoclingExtractor.assert_called_once()


def test_get_default_pdf_reader_uses_pdf_extractor(monkeypatch):
    reader = object()
    pdf = MagicMock()
    pdf.BasicPdfMarkdownExtractor.return_value = reader
    monkeypatch.setattr(qa, "try_import", lambda name: pdf)

    assert qa.get_default_pdf_reader(150, "layout") is reader
    pdf.BasicPdfMarkdownExtractor.assert_called_once_with(
        dpi=150, layout_model="layout"
    )
