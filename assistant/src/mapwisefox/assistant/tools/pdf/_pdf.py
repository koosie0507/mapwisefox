import re
from contextlib import AbstractContextManager
from pathlib import Path

import stopwords

from ._text_extractor import PdfTextExtractor
from ._layout_extractor import PdfLayoutExtractor
from ._types import LayoutBox, TextItem

EN_STOPWORDS = stopwords.get_stopwords("english")
SENTENCE_TERMINATION_RE = re.compile(r"(?<=[.!?])\s+", re.M)
NON_SENTENCE_TERMINATION_RE = re.compile(r"(?<=[^\s.!?])\s+(?=[^\s.!?])", re.M)
LINE_NUMBERING_RE = re.compile(r"(\n|\s)\d+?(?:\n|$)", re.M)
BIBLIOGRAPHY_SECTION_RE = re.compile(r"\b(references|bibliography|文献)\b", re.I)
SECTION_HEADER_RE = re.compile(
    r"((?:(?:[IVXLCDM]+)|\d+)(?:[.)](?:[a-z]+|\d+|(?:ix|iv|v?i{0,3}|xl|xc|cd|cm|d?c{0,3})))*[.)\n])\s*([^\n.?!]{,50})(?:[\n.?!]|$)",
    re.M,
)


class Paper(AbstractContextManager):
    def __init__(self, file: str | Path, dpi: int = 200):
        self.__file_path = Path(file).resolve()
        self._text_extractor = PdfTextExtractor()
        self._layout_extractor = PdfLayoutExtractor(dpi)
        self._text = ""

    @property
    def file_path(self) -> Path:
        return self.__file_path

    def __enter__(self):
        self._text_extractor(self.__file_path)
        self._layout_extractor(self.__file_path)
        scale_x = {
            page_no: p.width / self._layout_extractor.image_sizes[page_no].width
            for page_no, p in self._text_extractor.page_sizes.items()
        }
        scale_y = {
            page_no: p.height / self._layout_extractor.image_sizes[page_no].height
            for page_no, p in self._text_extractor.page_sizes.items()
        }
        scaled_boxes = {
            page_no: [
                LayoutBox(
                    type=box.type,
                    bounds=box.bounds.scale(scale_x[page_no], scale_y[page_no]),
                )
                for box in boxes
            ]
            for page_no, boxes in self._layout_extractor.page_layouts.items()
        }
        extracted_text_boxes = self._text_extractor.text_items
        self._text = self._merge_text_by_layout_overlap(
            extracted_text_boxes, scaled_boxes
        )
        return self

    def _merge_text_by_layout_overlap(
        self,
        extracted_text_boxes: dict[int, list[TextItem]],
        scaled_boxes: dict[int, list[LayoutBox]],
    ) -> str:
        """
        Retain and merge text items whose bounding boxes overlap at least one
        layout box on the same page. Text order is preserved as emitted by
        PdfTextExtractor.
        """

        def _priority(box_type: str) -> int:
            # higher value = higher priority
            return {"title": 3, "list": 2, "text": 1}.get(box_type, 0)

        def _merge_group(texts: list[str], box_type: str) -> str:
            if box_type == "title":
                return "\n**" + " ".join(texts).strip() + "**\n"
            if box_type == "list":
                return "\n".join(texts) + "\n"
            return " ".join(texts) + " "

        merged: list[str] = []

        for page_no, text_items in extracted_text_boxes.items():
            page_layout_boxes = scaled_boxes.get(page_no, [])
            if not page_layout_boxes:
                continue

            current_type: str | None = None
            current_texts: list[str] = []

            for item in text_items:
                item_bounds = item.bounds

                # collect all intersecting layout box types
                intersecting_types = [
                    lb.type.lower()
                    for lb in page_layout_boxes
                    if item_bounds.intersects(lb.bounds)
                ]

                if not intersecting_types:
                    continue

                # compress to highest-priority type
                item_type = max(intersecting_types, key=_priority)

                def _append_text(buf: list[str], new_text: str):
                    if not buf:
                        buf.append(new_text)
                        return
                    prev = buf[-1]
                    if prev.endswith("-"):
                        # merge hyphenated line break
                        buf[-1] = prev[:-1] + new_text.lstrip()
                    else:
                        buf.append(new_text)

                if current_type is None:
                    current_type = item_type
                    current_texts = []
                    _append_text(current_texts, item.text)
                elif item_type == current_type:
                    _append_text(current_texts, item.text)
                else:
                    merged.append(_merge_group(current_texts, current_type))
                    current_type = item_type
                    current_texts = []
                    _append_text(current_texts, item.text)

            # flush remainder for page
            if current_type and current_texts:
                merged.append(_merge_group(current_texts, current_type))

        return "".join(merged)

    def __exit__(self, exc_type, exc_value, traceback, /):
        pass

    @property
    def text(self) -> str:
        return self._text
