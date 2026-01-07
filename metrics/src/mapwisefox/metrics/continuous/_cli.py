from pathlib import Path

import click
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from mapwisefox.metrics._types import CommonArgs
from mapwisefox.metrics._utils import load_df
from mapwisefox.metrics._validators import validate_input_file_type
from mapwisefox.metrics.continuous._one_to_one import compute_metric


@click.command("mae")
@click.argument(
    "evaluated_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    callback=validate_input_file_type,
)
@click.pass_context
def mae(ctx: click.Context, evaluated_file: Path):
    common_args: CommonArgs = ctx.obj
    eval_df = load_df(evaluated_file, common_args.id_attr)
    metric_df = compute_metric(
        evaluated_file.stem,
        mean_absolute_error,
        common_args.input_dfs,
        eval_df,
        common_args.target_attrs,
    )

    with pd.ExcelWriter(
        common_args.output_file, if_sheet_exists="replace", mode="a", engine="openpyxl"
    ) as writer:
        metric_df.to_excel(writer, sheet_name="mean absolute error", index=False)


@click.command("rmse")
@click.argument(
    "evaluated_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    callback=validate_input_file_type,
)
@click.pass_context
def rmse(ctx: click.Context, evaluated_file: Path):
    common_args: CommonArgs = ctx.obj
    eval_df = load_df(evaluated_file, common_args.id_attr)
    metric_df = compute_metric(
        evaluated_file.stem,
        root_mean_squared_error,
        common_args.input_dfs,
        eval_df,
        common_args.target_attrs,
    )

    with pd.ExcelWriter(
        common_args.output_file, if_sheet_exists="replace", mode="a", engine="openpyxl"
    ) as writer:
        metric_df.to_excel(writer, sheet_name="root mean squared error", index=False)
