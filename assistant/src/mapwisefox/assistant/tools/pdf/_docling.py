import gc
from pathlib import Path

import torch
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.utils.model_downloader import download_models
from docling.document_converter import DocumentConverter, PdfFormatOption


class DoclingExtractor:
    def __init__(self, local_cache_path: Path | None = None):
        pdf_options = self.__pdf_pipeline_options(local_cache_path)
        self._format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_options)
        }

    @classmethod
    def __pdf_pipeline_options(cls, path: Path | None) -> PdfPipelineOptions:
        options = PdfPipelineOptions(generate_parsed_pages=False)

        if path is not None:
            path.mkdir(parents=True, exist_ok=True)
            download_models(output_dir=path)
            options.artifacts_path = path.resolve()

        return options

    def read_file(self, file: str | Path) -> str:
        fpath = Path(file).resolve()
        converter = DocumentConverter(format_options=self._format_options)
        conversion_result = converter.convert(fpath)
        try:
            doc = conversion_result.document
            return doc.export_to_markdown()
        finally:
            conversion_result.input._backend.unload()
            del converter
            torch.mps.empty_cache()
            gc.collect()
