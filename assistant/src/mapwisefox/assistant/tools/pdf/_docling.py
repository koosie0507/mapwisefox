import gc
from pathlib import Path
from typing import Callable

import torch
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.exceptions import ConversionError
from docling.utils.model_downloader import download_models
from docling.document_converter import DocumentConverter, PdfFormatOption

from mapwisefox.assistant.tools.pdf._base import FileContentsExtractor


class DoclingExtractor(FileContentsExtractor):
    def __init__(
        self,
        local_cache_path: Path | None = None,
        error_callback: Callable | None = None,
    ):
        pdf_options = self.__pdf_pipeline_options(local_cache_path)
        self._format_options = self.__create_format_options(pdf_options)
        self._error_callback = error_callback or self.__no_op

    @classmethod
    def __no_op(cls, *_, **__):
        pass

    @classmethod
    def __create_format_options(
        cls, pdf_options: PdfPipelineOptions
    ) -> dict[InputFormat, PdfFormatOption]:
        return {InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)}

    @classmethod
    def __pdf_pipeline_options(cls, path: Path | None) -> PdfPipelineOptions:
        options = PdfPipelineOptions(
            generate_parsed_pages=False,
            do_ocr=True,
            do_table_structure=True,
            generate_picture_images=False,
            generate_table_images=False,
            generate_page_images=False,
            images_scale=1.0,
        )

        if path is not None:
            path.mkdir(parents=True, exist_ok=True)
            download_models(output_dir=path)
            options.artifacts_path = path.resolve()

        return options

    def read_file(self, file: str | Path) -> str:
        backend = None
        fpath = Path(file).resolve()
        converter = DocumentConverter(format_options=self._format_options)
        try:
            conversion_result = converter.convert(fpath)
            backend = conversion_result.input._backend
            doc = conversion_result.document
            return doc.export_to_markdown()
        except ConversionError:
            self._error_callback("failed to convert %r", file)
            raise
        except Exception as exc:
            self._error_callback("failed to process %r: %s", file, exc)
            raise
        finally:
            if backend is not None:
                backend.unload()
            del converter
            torch.mps.empty_cache()
            gc.collect()
