import shutil
from collections import defaultdict
from pathlib import Path
from types import ModuleType

from layoutparser.elements import layout_elements
from layoutparser.models import AutoLayoutModel
from PIL import ImageDraw

from ._types import LayoutBox, Rect, Point, Size


class PdfLayoutExtractor:
    @staticmethod
    def __ensure_poppler() -> ModuleType:
        """
        Layout inference requires rendering PDF pages to images.
        We currently rely on pdf2image + Poppler (pdftoppm/pdftocairo) for that.
        """
        try:
            import pdf2image  # noqa: F401
        except Exception as e:
            raise RuntimeError(
                r"""Layout inference requires the optional dependency 'pdf2image' and the Poppler tools.

Install:
  pip install pdf2image

And install Poppler (provides 'pdftoppm' / 'pdftocairo')
  - Ubuntu/Debian: sudo apt-get install poppler-utils
  - macOS (Homebrew): brew install poppler
  - Windows: install Poppler and add its 'bin' directory to PATH
"""
            ) from e

        if shutil.which("pdftoppm") is None and shutil.which("pdftocairo") is None:
            raise RuntimeError(
                r"""Layout inference requires Poppler, but 'pdftoppm'/'pdftocairo' was not found on PATH.

Install Poppler:
  - Ubuntu/Debian: sudo apt-get install poppler-utils
  - macOS (Homebrew): brew install poppler
  - Windows: install Poppler and add its 'bin' directory to PATH

Then re-run the extractor."""
            )
        return pdf2image

    def __init__(
        self,
        dpi: int = 200,
        debug_images: bool = False,
        debug_dir: str | Path = "_layout_debug",
    ):
        self._layout_boxes: dict[int, list[LayoutBox]] = defaultdict(list)
        self._debug_images = debug_images
        self._debug_dir = Path(debug_dir)
        self._image_sizes: dict[int, Size] = {}
        self._dpi = dpi

    @property
    def image_sizes(self) -> dict[int, Size]:
        return self._image_sizes

    @property
    def page_layouts(self) -> dict[int, list[LayoutBox]]:
        return self._layout_boxes

    @classmethod
    def __is_supported(cls, element: layout_elements.TextBlock) -> bool:
        return element.type in {"Text", "List", "Title"}

    @classmethod
    def __to_layout_box(cls, element: layout_elements.TextBlock) -> LayoutBox:
        x0, y0, x1, y1 = element.block.coordinates
        return LayoutBox(type=element.type, bounds=Rect(Point(x0, y0), Point(x1, y1)))

    def __call__(self, file: str | Path) -> Path:
        pdf2image = self.__ensure_poppler()
        self._image_sizes.clear()
        self._layout_boxes.clear()
        file_path = Path(file).resolve()

        # Render pages
        images = pdf2image.convert_from_path(str(file_path), dpi=self._dpi)

        if self._debug_images:
            self._debug_dir.mkdir(parents=True, exist_ok=True)

        # Initialize a basic layout model from layoutparser
        # Here we use a PubLayNet model from the LayoutParser model zoo
        model = AutoLayoutModel(
            config_path="lp://PubLayNet/tf_efficientdet_d0/config",
            label_map={1: "Text", 2: "Title", 3: "List", 4: "Table", 5: "Figure"},
            device="cuda",  # or "cpu"
            extra_config={"output_confidence_threshold": 0.25},
        )

        for page_no, image in enumerate(images):
            self._image_sizes[page_no] = Size(*image.size)
            layout = model.detect(image)

            elements = list(filter(self.__is_supported, layout))
            boxes = list(map(self.__to_layout_box, elements))
            self._layout_boxes[page_no] = boxes

            if self._debug_images:
                img = image.copy()
                draw = ImageDraw.Draw(img)
                cmap = {
                    "Text": "red",
                    "Title": "yellow",
                    "List": "blue",
                }
                for el in elements:
                    x0, y0, x1, y1 = el.block.coordinates
                    draw.rectangle(
                        [(x0, y0), (x1, y1)],
                        outline=cmap[el.type],
                        width=2,
                    )

                out_path = self._debug_dir / f"page_{page_no:04d}.png"
                img.save(out_path)
        return file_path
