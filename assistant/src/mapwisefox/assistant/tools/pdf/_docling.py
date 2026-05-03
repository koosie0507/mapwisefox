import gc
from multiprocessing import Lock, Pipe, Process
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Callable

import torch
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.exceptions import ConversionError
from docling.utils.model_downloader import download_models
from docling.document_converter import DocumentConverter, PdfFormatOption

from mapwisefox.assistant.tools.pdf._base import (
    FileContentsExtractor,
    FileContentsExtractionError,
    ExtractionFailureReason,
)


class DoclingExtractor(FileContentsExtractor):
    def __init__(
        self,
        docling_artifacts_path: Path | None = None,
        error_callback: Callable | None = None,
        timeout_seconds: float = 60.0,
    ):
        pdf_options = self.__pdf_pipeline_options(docling_artifacts_path)
        self._format_options = self.__create_format_options(pdf_options)
        self._error_callback = error_callback or self._noop_error_callback
        self._timeout_seconds = timeout_seconds
        self.__lock = Lock()

    @classmethod
    def _noop_error_callback(cls, *_, **__):
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

    def _docling_process(self, conn: Connection, fpath: Path):
        backend = None
        converter = DocumentConverter(format_options=self._format_options)
        try:
            conversion_result = converter.convert(fpath)
            backend = conversion_result.input._backend
            doc = conversion_result.document
            conn.send(doc.export_to_markdown())
        except ConversionError:
            self._error_callback("failed to convert %r", fpath.name)
            conn.send("conversion error")
            raise
        except Exception as exc:
            self._error_callback("failed to process %r: %s", fpath.name, exc)
            conn.send("unhandled error")
            raise
        finally:
            if backend is not None:
                backend.unload()
                del backend
            del converter
            torch.mps.empty_cache()
            gc.collect()

    def read_file(self, file: str | Path) -> str:
        result = ""
        timed_out = True
        try:
            fpath = Path(file).resolve()
            self.__lock.acquire()
            recv_conn, send_conn = Pipe()
            process = Process(
                target=self._docling_process,
                args=(send_conn, fpath),
            )
            process.start()

            if recv_conn.poll(timeout=self._timeout_seconds):
                result = recv_conn.recv()
                timed_out = False
            else:
                process.terminate()
            process.join()
        except Exception as exc:
            raise FileContentsExtractionError(
                ExtractionFailureReason.Generic, file, str(exc)
            )
        finally:
            self.__lock.release()

        if timed_out:
            raise FileContentsExtractionError(ExtractionFailureReason.Timeout, fpath)
        if process.exitcode != 0:
            raise FileContentsExtractionError(
                ExtractionFailureReason.BackendError, fpath, result
            )

        return result


if __name__ == "__main__":
    e = DoclingExtractor(timeout_seconds=60.0)
    print(
        e.read_file(
            "./uploads/downloads/dagade2017-7be7c7f52f6138c479c8c3e313db3837.pdf"
        )
    )
