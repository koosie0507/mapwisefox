import itertools
import os
import shutil
from concurrent.futures import ProcessPoolExecutor, wait
from collections import defaultdict
from functools import partial
from pathlib import Path
from types import ModuleType

from PIL.PpmImagePlugin import PpmImageFile
from layoutparser.elements import layout_elements
from layoutparser.models import AutoLayoutModel
from PIL import ImageDraw

from mapwisefox.assistant.tools.pdf._types import LayoutBox, Rect, Point, Size


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
        min_merge_overlap_ratio=0.5,
        debug: bool = False,
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
        :param min_merge_overlap_ratio: the layout extractor will merge two
        boxes if the area of the intersection of the two boxes overlaps the
        smaller one of the boxes at least by this factor. Default=**``0.9``**.
        :param debug: whether to generate debug images with layout boxes plotted
        on the extracted PDF page. Default=**``False``**
        """
        self.__config_path = config_path
        self.__label_map = label_map or {
            1: "Text",
            2: "Title",
            3: "List",
            4: "Table",
            5: "Figure",
        }
        self.__overlap_min = min_merge_overlap_ratio
        self.__layout_boxes: dict[int, list[LayoutBox]] = defaultdict(list)
        self.__image_sizes: dict[int, Size] = {}
        self.__dpi = dpi
        self.__init_debug_images__(debug)

    def __init_debug_images__(self, debug: bool):
        self._debug = debug
        if self._debug:
            cycle_colors = itertools.cycle(
                ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
            )
            self._debug_color_map = {
                label_value: next(cycle_colors)
                for label_value in self.__label_map.values()
            }
        else:
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
        return LayoutBox(
            types=[], bounds=Rect(Point(x0, y0), Point(x1, y1))
        ).ensure_type(element.type)

    def __greedy_overlap_merge(self, boxes: list[LayoutBox]) -> list[LayoutBox]:
        q = list(boxes)
        result = []
        while len(q) > 0:
            current = q.pop(0)
            i = 0
            while i < len(q):
                candidate = q[i]
                if current.bounds.overlap_ratio(candidate.bounds) >= self.__overlap_min:
                    current = current.union(candidate)
                    del q[i]
                    i = 0
                else:
                    i += 1
            result.append(current)
        return result

    def _process_page(self, file_path: Path, model, page_no: int, image):
        layout = model.detect(image)
        return self.__greedy_overlap_merge(
            list(map(self.__to_layout_box, filter(self.__is_supported, layout)))
        )

    def __call__(
        self,
        file: str | Path,
        first_page: int | None = None,
        last_page: int | None = None,
    ) -> Path:
        pdf2image = self.__ensure_poppler()
        self.__image_sizes.clear()
        self.__layout_boxes.clear()
        file_path = Path(file).resolve()

        model = AutoLayoutModel(
            config_path=self.__config_path,
            label_map=self.__label_map,
            device="cuda",  # or "cpu"
            extra_config={"output_confidence_threshold": 0.25},
        )

        images = pdf2image.convert_from_path(
            file_path, dpi=self.__dpi, first_page=first_page, last_page=last_page
        )
        executor = ProcessPoolExecutor(max_workers=os.cpu_count() - 1)

        futures = {}
        for page_no, image in enumerate(images):
            self.__image_sizes[page_no] = Size(image.size[0], image.size[1])
            process_page = partial(self._process_page, file_path, model)
            futures[page_no] = executor.submit(process_page, page_no, image)
        wait(futures.values())

        for page_no, image in enumerate(images):
            self.__layout_boxes[page_no] = futures[page_no].result()
            self._write_debug_image(file_path, page_no, image)

        return file_path

    def _write_debug_image(
        self, file_path: Path, page_no: int, page_image: PpmImageFile
    ):
        if not self._debug:
            return
        img = page_image.copy()
        draw = ImageDraw.Draw(img)
        for box in self.__layout_boxes[page_no]:
            colors = [self._debug_color_map[t] for t in box.types]
            w = 2
            for i, color in enumerate(colors):
                padding = 2 * w * i
                draw.rectangle(
                    [
                        (box.bounds.start.x - padding, box.bounds.start.y - padding),
                        (box.bounds.end.x + padding, box.bounds.end.y + padding),
                    ],
                    outline=colors[i],
                    width=w,
                )
        debug_dir = file_path.parent / f"debug_{file_path.stem}"
        debug_dir.mkdir(exist_ok=True)
        out_path = debug_dir / f"page_{page_no:04d}.png"
        img.save(out_path)


if __name__ == "__main__":
    extract = PdfLayoutExtractor(
        config_path="lp://PubLayNet/tf_efficientdet_d1/config", debug=True
    )
    extract("./uploads/nguyen2016.pdf")  # , first_page=7, last_page=7)
