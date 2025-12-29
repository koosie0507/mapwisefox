from pathlib import Path

import click

from mapwisefox.assistant._base import assistant
from mapwisefox.assistant.tools.pdf import (
    PdfTextFileExtractor,
    PdfMarkdownFileExtractor,
)


@assistant.command("judge")
@click.argument(
    "file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.option(
    "-f",
    "--format",
    "file_format",
    type=click.Choice(choices=["txt", "md"]),
    default="txt",
    help="output format",
)
@click.pass_context
def judge(ctx, file: Path, file_format: str):
    file = Path(file).resolve()
    extractor = (
        PdfTextFileExtractor() if file_format == "txt" else PdfMarkdownFileExtractor()
    )
    output_path = file.parent / f"{file.stem}.{file_format}"
    with open(output_path, "w") as fp:
        fp.write(extractor.read_file(file))
