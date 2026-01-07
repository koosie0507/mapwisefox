from dataclasses import dataclass, field
from pathlib import Path

import click
import pandas as pd

import mapwisefox.metrics._utils as util
from mapwisefox.metrics.categorical import kappa_score


@dataclass
class GroupArgs:
    input_files: list[Path] = field(default_factory=list)
    target_attrs: list[str] = field(default_factory=list)
    id_attr: str = "id"
    output_file: Path = ""
    extra_cols: list[str] = field(default_factory=list)
    input_dfs: list[pd.DataFrame] = field(default_factory=list)


def _validate_input_file_types(_, param, value):
    if param.name != "input_files":
        return value
    input_files = [Path(x).resolve() for x in value]
    for path in input_files:
        if path.suffix in util.SUPPORTED_FILE_HANDLERS:
            continue
        raise click.BadParameter(f"unsupported file type {path.suffix!r}")
    return input_files


def _validate_output_file_type(_, param, value):
    if param.name != "output_file":
        return value
    output_path = Path(value).resolve()
    if output_path.suffix != ".xls":
        raise click.BadParameter("will output only .xls files")
    return output_path


def _load_dataframes(ctx, input_files: list[Path], id_attr: str) -> list[pd.DataFrame]:
    result = []
    for file_path in input_files:
        try:
            result.append(util.load_df(file_path, id_attr))
        except Exception as exc:
            message = f"could not load file {file_path.name!r}: {exc}"
            raise click.BadOptionUsage("id_attr", message, ctx)
    return result


@click.group("metrics")
@click.option(
    "-i",
    "--input-file",
    "input_files",
    type=click.Path(exists=True, readable=True, dir_okay=False, file_okay=True),
    multiple=True,
    callback=_validate_input_file_types,
    help="files to use as input to the metrics",
)
@click.option(
    "-t",
    "--target-value",
    "target_attrs",
    type=str,
    multiple=True,
    help="columns/attributes existing in *all* input files which contain the target values",
    required=True,
)
@click.option(
    "-k",
    "--key-attr",
    type=str,
    default="id",
    help="a column/attribute which exists in all input files and identifies each record",
)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(writable=True, file_okay=True, dir_okay=False),
    callback=_validate_input_file_types,
    help="file where to output the computed metrics",
)
@click.option(
    "-x",
    "--extra-column",
    "extra_columns",
    type=str,
    multiple=True,
    help="optional extra columns to concatenate and include in the output file",
)
@click.pass_context
def metrics(
    ctx: click.Context,
    input_files: list[Path],
    target_attrs: list[str],
    key_attr: str,
    output_file: Path,
    extra_columns: list[str],
) -> None:
    obj = ctx.ensure_object(GroupArgs)
    obj.input_files = input_files
    obj.target_attrs = target_attrs
    obj.id_attr = key_attr
    obj.output_file = output_file
    obj.extra_cols = extra_columns

    obj.input_dfs = _load_dataframes(ctx, input_files, key_attr)


metrics.add_command(kappa_score, "kappa-score")
