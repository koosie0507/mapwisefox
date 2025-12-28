from pathlib import Path

import click

from mapwisefox.assistant._base import assistant
from mapwisefox.assistant.tools.pdf import PdfTextFileExtractor


@assistant.command("judge")
@click.argument(
    "file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.pass_context
def judge(ctx, file: Path):
    file = Path(file).resolve()
    extractor = PdfTextFileExtractor()
    output_path = file.parent / f"{file.stem}.txt"
    with open(output_path, "w") as fp:
        fp.write(extractor.read_file(file))
