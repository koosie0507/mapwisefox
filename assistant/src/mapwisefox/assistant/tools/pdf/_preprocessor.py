import os
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def ensure_page_dimensions(file_path: Path) -> None:
    """Ensure that the .pdf file reports page dimensions for each page.

    Tools like Docling expect each page to have explicit dimensions in older
    versions. This function ensures that they get what they expect.

    :param file_path: path to the file which should be modified to include page
            dimensions. The modifications are made in-place.
    """
    with open(file_path, "rb+") as f:
        backup = f.read()
        reader = PdfReader(f)
        writer = PdfWriter()
        try:
            for page in reader.pages:
                cropbox = page.cropbox
                fallback = (
                    cropbox
                    if cropbox.width > 0 and cropbox.height > 0
                    else page.mediabox
                )
                page.mediabox = fallback
                page.cropbox = fallback
                writer.add_page(page)
            f.seek(0, os.SEEK_SET)
            f.truncate()
            writer.write(f)
        except Exception as e:
            f.seek(0, os.SEEK_SET)
            f.truncate()
            f.write(backup)
            raise e
        finally:
            reader.close()
            writer.close()
