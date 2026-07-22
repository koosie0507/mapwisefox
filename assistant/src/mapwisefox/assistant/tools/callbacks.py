import logging
from typing import Callable

import click


def write_stdout(msg: str, *args) -> None:
    output_text = msg % args if args else msg
    click.echo(output_text, nl=False)


def make_thinking_callback() -> Callable[[str], None]:
    wrote_label = False

    def _(msg: str) -> None:
        nonlocal wrote_label
        if not wrote_label:
            click.secho("Thinking ... ", nl=True, color=True, fg="blue", italic=True)
        click.secho(msg, nl=False, color=True, fg="blue", italic=True)
        wrote_label = True

    return _


def make_stderr_callback(logger: logging.Logger) -> Callable[[str, Exception], None]:
    def _(msg: str, err: Exception) -> None:
        logger.error(msg, exc_info=err)

    return _
