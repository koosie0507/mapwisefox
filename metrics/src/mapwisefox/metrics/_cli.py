from pathlib import Path

import click
import pandas as pd

import mapwisefox.metrics._utils as util
from mapwisefox.metrics._types import CommonArgs
from mapwisefox.metrics.categorical import kappa_score

from mapwisefox.metrics._validators import (
    validate_input_file_type,
    validate_output_file_type,
)
from mapwisefox.metrics.continuous import mae, rmse, ccc, icc_cli


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
    callback=validate_input_file_type,
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
    callback=validate_output_file_type,
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
    obj = ctx.ensure_object(CommonArgs)
    obj.input_files = input_files
    obj.target_attrs = target_attrs
    obj.id_attr = key_attr
    obj.output_file = output_file
    obj.extra_cols = extra_columns

    obj.input_dfs = _load_dataframes(ctx, input_files, key_attr)


metrics.add_command(kappa_score, "kappa-score")
metrics.add_command(mae, "mae")
metrics.add_command(rmse, "rmse")
metrics.add_command(ccc, "lin-ccc")
metrics.add_command(icc_cli, "icc")
