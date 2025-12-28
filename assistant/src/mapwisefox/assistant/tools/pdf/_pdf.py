import abc
from pathlib import Path

from ._text_extractor import PdfTextExtractor
from ._layout_extractor import PdfLayoutExtractor
from ._types import LayoutBox, TextItem


class PdfFileExtractor(metaclass=abc.ABCMeta):
    def __init__(
        self,
        dpi: int = 150,
        text_to_layout_min_overlap_ratio: float = 0.5,
    ):
        self._min_overlap_ratio = text_to_layout_min_overlap_ratio
        self.__text_extractor = PdfTextExtractor()
        self.__layout_extractor = PdfLayoutExtractor(dpi)

    def __compute_text_to_layout_scale(self) -> dict[int, tuple[float, float]]:
        return {
            page_no: (
                p.width / self.__layout_extractor.image_sizes[page_no].width,
                p.height / self.__layout_extractor.image_sizes[page_no].height,
            )
            for page_no, p in self.__text_extractor.page_sizes.items()
        }

    def __compute_boxes_by_page(
        self, scale: dict[int, tuple[float, float]]
    ) -> dict[int, tuple[list[LayoutBox], list[TextItem]]]:
        boxes_by_page = {
            page_no: (
                [box.scale(scale[page_no][0], scale[page_no][1]) for box in boxes],
                self.__text_extractor.text_items.get(page_no, []),
            )
            for page_no, boxes in self.__layout_extractor.page_layouts.items()
        }
        return boxes_by_page

    @abc.abstractmethod
    def _prepare_text(
        self, by_page: dict[int, tuple[list[LayoutBox], list[TextItem]]]
    ) -> str:
        pass

    def read_file(self, file: str | Path) -> str:
        fpath = Path(file).resolve()

        self.__text_extractor(fpath)
        self.__layout_extractor(fpath)

        scale = self.__compute_text_to_layout_scale()
        boxes_by_page = self.__compute_boxes_by_page(scale)

        return self._prepare_text(boxes_by_page)


class PdfTextFileExtractor(PdfFileExtractor):
    @staticmethod
    def __layout_type_priority(box_type: str) -> int:
        box_type = box_type.lower().strip()
        return {"title": 3, "list": 2, "text": 1}.get(box_type, -1)

    @staticmethod
    def __to_string(box_type: str, texts: list[str]) -> str:
        if box_type == "title":
            return "\n**" + " ".join(texts).strip() + "**\n"
        if box_type == "list":
            return "\n".join(texts) + "\n"
        return " ".join(texts) + " "

    @staticmethod
    def __append_text(existing: list[str], new_text: str) -> list[str]:
        if len(existing) > 0:
            prev = existing[-1].strip()
            if prev.endswith("-"):
                existing[-1] = prev[:-1] + new_text.lstrip()
            else:
                existing.append(new_text)
        else:
            existing.append(new_text)
        return existing

    def __find_overlaps(self, text_item: TextItem, boxes: list[LayoutBox]):
        return [
            box
            for box in boxes
            if box.bounds.overlap_ratio(text_item.bounds) >= self._min_overlap_ratio
        ]

    def _prepare_text(
        self, by_page: dict[int, tuple[list[LayoutBox], list[TextItem]]]
    ) -> str:
        merged: list[str] = []
        current_type: str | None = None
        current_texts: list[str] = []

        for page_no, (layout_boxes, text_items) in by_page.items():
            for text_item in text_items:
                overlapping_boxes = self.__find_overlaps(text_item, layout_boxes)
                if len(overlapping_boxes) < 1:
                    continue
                box_type = max(
                    (t for box in overlapping_boxes for t in box.types),
                    key=self.__layout_type_priority,
                )

                if current_type != box_type:
                    if len(current_texts) > 0:
                        merged.append(self.__to_string(current_type, current_texts))
                    current_type = box_type
                    current_texts = []

        if len(current_texts) > 0:
            merged.append(self.__to_string(current_type, current_texts))

        return "".join(merged)
