import click

from mapwisefox.assistant._base import assistant
from mapwisefox.assistant.tools import PaperPdf


@assistant.command("judge")
@click.argument(
    "file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
)
@click.pass_context
def judge(ctx, file):
    with PaperPdf(file) as p:
        print(p.text)
