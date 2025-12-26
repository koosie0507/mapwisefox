import click

from mapwisefox.assistant._base import assistant
from mapwisefox.assistant.tools import extract_pdf_text


@assistant.command("judge")
@click.argument(
    "file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.pass_context
def judge(ctx, file):
    text = extract_pdf_text(file)
    print(text)