from pathlib import Path

from docling.document_converter import DocumentConverter


class DoclingExtractor:
    def __init__(self):
        self._converter = DocumentConverter()

    def read_file(self, file: str | Path) -> str:
        fpath = Path(file).resolve()
        conversion_result = self._converter.convert(fpath)
        doc = conversion_result.document
        return doc.export_to_markdown()