import math
from collections import defaultdict
from functools import partial
from pathlib import Path

from pypdf import PdfReader

from ._types import *


class PdfTextExtractor:
    def __init__(self):
        self._page_sizes: dict[int, Size] = {}
        self._text_items: dict[int, list[TextItem]] = defaultdict(list)

    @property
    def text_items(self) -> dict[int, list[TextItem]]:
        return self._text_items

    @property
    def page_sizes(self) -> dict[int, Size]:
        return self._page_sizes

    @classmethod
    def __apply_matrix(cls, m: list[float], x: float, y: float) -> Point:
        a, b, c, d, e, f = m
        return Point(
            a * x + c * y + e,
            b * x + d * y + f,
        )

    @classmethod
    def __compute_font_size(cls, font_size, user_matrix) -> float:
        a, b, c, d, _, _ = user_matrix
        det = a * d - b * c
        scale = math.sqrt(det) if det > 0 else abs(d)
        return font_size * scale

    @classmethod
    def __compute_ascent_descent(
        cls, font_dictionary: dict | None
    ) -> tuple[float, float]:
        ascent = 0.8
        descent = 0.2
        if font_dictionary is None:
            return ascent, descent
        bbox = font_dictionary.get("/FontBBox")
        if bbox is None or len(bbox) != 4:
            return ascent, descent
        y_min, y_max = bbox[1], bbox[3]
        if y_max <= y_min:
            return ascent, descent

        ascent = y_max / 1000.0
        descent = abs(y_min) / 1000.0
        return ascent, descent

    @classmethod
    def __estimate_text_width(
        cls, font_dictionary: dict | None, font_size: float, text: str
    ) -> float:
        if text is None or not text.strip():
            return 0.0

        if font_dictionary is None or not (
            (widths := font_dictionary.get("/Widths")) and (isinstance(widths, list))
        ):
            avg_char_width = 0.55 * font_size
            return avg_char_width * len(text)

        first_char = font_dictionary.get("/FirstChar", 0)
        total = 0.0
        for ch in text:
            cid = ord(ch) - first_char
            if 0 <= cid < len(widths):
                total += widths[cid]
            else:
                total += 500
        # Convert from 1/1000 em to user space
        return (total / 1000.0) * font_size

    @classmethod
    def __compute_text_size(
        cls, text: str, font_size: float, font_dictionary: dict | None
    ) -> Size:
        ascent, descent = cls.__compute_ascent_descent(font_dictionary)
        text_height = (ascent + descent) * font_size
        text_width = cls.__estimate_text_width(font_dictionary, font_size, text)

        return Size(text_width, text_height)

    @classmethod
    def __from_top_left(
        cls, page_height: float, origin: Point, text_size: Size
    ) -> Rect:
        return Rect(
            start=Point(origin.x, page_height - origin.y - text_size.height),
            end=Point(origin.x + text_size.width, page_height - origin.y),
        )

    def __visit_text(
        self, page, text, user_matrix, text_matrix, font_dictionary, font_size
    ):
        if text is None or not str(text).strip():
            return

        # get translation from text_matrix
        _, _, _, _, tx, ty = text_matrix
        # map the coordinates to user-space (given by user_matrix)
        origin = self.__apply_matrix(user_matrix, tx, ty)
        actual_font_size = self.__compute_font_size(font_size, user_matrix)
        text_size = self.__compute_text_size(text, actual_font_size, font_dictionary)
        page_size = self._page_sizes[page]
        text_bounds = self.__from_top_left(page_size.height, origin, text_size)

        # remove headers and footers
        y_norm = text_bounds.vertical_norm(page_size.height)
        if y_norm < 0.1 or y_norm > 0.9:
            return

        text_item = TextItem(
            text=text,
            font_size=actual_font_size,
            font_dict=font_dictionary,
            bounds=text_bounds,
        )

        self._text_items[page].append(text_item)

    def __call__(self, file: str | Path) -> Path:
        self._page_sizes.clear()
        self._text_items.clear()
        file_path = Path(file).resolve()
        with PdfReader(file_path) as r:
            for page_number, page in enumerate(r.pages):
                _, _, page_w, page_h = map(float, page.mediabox)
                self._page_sizes[page_number] = Size(page_w, page_h)
                visit_page_text = partial(self.__visit_text, page_number)
                page.extract_text(visitor_text=visit_page_text)
        return file_path
