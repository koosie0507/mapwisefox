import click

from mapwisefox.common.config import (
    ConfigValidationError,
    load_qa_config,
    load_selection_config,
)


_LOADERS = {
    "study-selection": load_selection_config,
    "study-qa": load_qa_config,
}


@click.command(
    "validate-config",
    help=r"""Validate a study-selection or study-qa JSON configuration file.

The configuration file is checked against the same schema used by the
corresponding command locally, without contacting any LLM provider.
The JSON Schema files are publicly available under common-config/schemas for
editor/IDE integration.""",
)
@click.option(
    "-k",
    "--kind",
    type=click.Choice(list(_LOADERS)),
    required=True,
    help="which command's configuration file to validate",
)
@click.option(
    "-c",
    "--config-file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
    required=True,
    help="path to the JSON configuration file to validate",
)
def validate_config(kind, config_file):
    try:
        _LOADERS[kind](config_file)
    except ConfigValidationError as err:
        raise click.ClickException(str(err))
    click.echo(f"Configuration is valid: {config_file}")
