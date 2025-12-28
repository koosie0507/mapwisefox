import itertools
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
        dpi: int = 150,
        config_path: str = "lp://PubLayNet/tf_efficientdet_d0/config",
        label_map: dict[int, str] = None,
        debug: bool = False,
        debug_dir: str | Path = None,
    ):
        """Initialize a new layout extractor.

        The layout extractor works by creating images from each PDF page and
        running a layout detection model via the ``layoutparser`` package.

        :param dpi: the resolution to use when extracting the images for each
            PDF page (higher resolutions yield better quality, but have slower
            processing times). Default=**``150``**
        :param config_path: the ``layoutparser`` model to use. By default, we
        install ``layoutparser`` as a dependency with the ``layoutmodels`` and
        ``effdet`` extras. Additional work is required to use **DetectronV2**
        models. Default=**``lp://PubLayNet/tf_efficientdet_d0/config``**
        :param label_map: a custom label map to pass to the layout detection
        model. Default=**``None``**
        :param debug: whether to generate debug images with layout boxes plotted
        on the extracted PDF page. Default=**``False``**
        :param debug_dir: where to save the images. By default, these are saved
        in the `_layout_debug` subdirectory of the current working directory.
        Default=**``None``**.
        """
        self.__config_path = config_path
        self.__label_map = label_map or {
            1: "Text",
            2: "Title",
            3: "List",
            4: "Table",
            5: "Figure",
        }
        self.__layout_boxes: dict[int, list[LayoutBox]] = defaultdict(list)
        self.__image_sizes: dict[int, Size] = {}
        self.__dpi = dpi
        self.__init_debug_images__(debug, debug_dir)

    def __init_debug_images__(self, debug: bool, debug_dir: str | Path | None):
        self._debug = debug
        if self._debug:
            self._debug_dir = (
                Path(debug_dir).resolve() if debug_dir else Path.cwd() / "_layout_debug"
            )
            cycle_colors = itertools.cycle(
                ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
            )
            self._debug_color_map = {
                label_value: next(cycle_colors)
                for label_value in self.__label_map.values()
            }
        else:
            self._debug_dir = None
            self._debug_color_map = None

    @property
    def image_sizes(self) -> dict[int, Size]:
        return self.__image_sizes

    @property
    def page_layouts(self) -> dict[int, list[LayoutBox]]:
        return self.__layout_boxes

    @classmethod
    def __is_supported(cls, element: layout_elements.TextBlock) -> bool:
        return element.type in {"Text", "List", "Title"}

    @classmethod
    def __to_layout_box(cls, element: layout_elements.TextBlock) -> LayoutBox:
        x0, y0, x1, y1 = element.block.coordinates
        return LayoutBox(type=element.type, bounds=Rect(Point(x0, y0), Point(x1, y1)))

    def __call__(self, file: str | Path) -> Path:
        pdf2image = self.__ensure_poppler()
        self.__image_sizes.clear()
        self.__layout_boxes.clear()
        file_path = Path(file).resolve()

        # Render pages
        images = pdf2image.convert_from_path(str(file_path), dpi=self.__dpi)

        if self._debug:
            self._debug_dir.mkdir(parents=True, exist_ok=True)

        # Initialize a basic layout model from layoutparser
        # Here we use a PubLayNet model from the LayoutParser model zoo
        model = AutoLayoutModel(
            config_path=self.__config_path,
            label_map=self.__label_map,
            device="cuda",  # or "cpu"
            extra_config={"output_confidence_threshold": 0.25},
        )

        for page_no, image in enumerate(images):
            self.__image_sizes[page_no] = Size(image.size[0], image.size[1])
            layout = model.detect(image)
            boxes = list(map(self.__to_layout_box, filter(self.__is_supported, layout)))
            self.__layout_boxes[page_no] = boxes
            self._write_debug_image(page_no, image)
        return file_path

    def _write_debug_image(self, page_no: int, page_image):
        if not self._debug:
            return
        img = page_image.copy()
        draw = ImageDraw.Draw(img)
        for box in self.__layout_boxes[page_no]:
            draw.rectangle(
                [
                    (box.bounds.start.x, box.bounds.start.y),
                    (box.bounds.end.x, box.bounds.end.y),
                ],
                outline=self._debug_color_map[box.type],
                width=2,
            )

        out_path = self._debug_dir / f"page_{page_no:04d}.png"
        img.save(out_path)
