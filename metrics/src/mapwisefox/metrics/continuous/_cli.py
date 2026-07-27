from functools import partial
from pathlib import Path

import click
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from mapwisefox.metrics._types import CommonArgs
from mapwisefox.metrics._utils import load_df
from mapwisefox.metrics._validators import validate_input_file_type
from mapwisefox.metrics.continuous._ccc import lin_ccc
from mapwisefox.metrics.continuous._cli_util import save_xls
from mapwisefox.metrics.continuous._icc import icc, ICCType
from mapwisefox.metrics.continuous._many_to_many import compute_many_metrics
from mapwisefox.metrics.continuous._one_to_one import compute_metric


def _print_metric_df(
    metric_df: "pd.DataFrame", metric_name: str, evaluated_file: Path
) -> None:
    click.echo(f"{metric_name} for {evaluated_file.stem}:")
    click.echo(metric_df.to_string(index=False))


@click.command(
    "mae",
    help="Compute Mean Absolute Error between a new rater and a ground truth built from trusted raters.",
)
@click.argument(
    "evaluated_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    callback=validate_input_file_type,
)
@click.pass_context
def mae(ctx: click.Context, evaluated_file: Path):
    """Compare EVALUATED_FILE against the mean, minimum and maximum of the trusted input raters."""
    common_args: CommonArgs = ctx.obj
    eval_df = load_df(evaluated_file, common_args.id_attr)
    metric_df = compute_metric(
        evaluated_file.stem,
        mean_absolute_error,
        common_args.input_dfs,
        eval_df,
        common_args.target_attrs,
    )

    _print_metric_df(metric_df, "Mean Absolute Error", evaluated_file)
    save_xls(metric_df, common_args, "Mean Absolute Error")


@click.command(
    "rmse",
    help="Compute Root Mean Squared Error between a new rater and a ground truth built from trusted raters.",
)
@click.argument(
    "evaluated_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    callback=validate_input_file_type,
)
@click.pass_context
def rmse(ctx: click.Context, evaluated_file: Path):
    """Compare EVALUATED_FILE against the mean, minimum and maximum of the trusted input raters."""
    common_args: CommonArgs = ctx.obj
    eval_df = load_df(evaluated_file, common_args.id_attr)
    metric_df = compute_metric(
        evaluated_file.stem,
        root_mean_squared_error,
        common_args.input_dfs,
        eval_df,
        common_args.target_attrs,
    )

    _print_metric_df(metric_df, "Root Mean Squared Error", evaluated_file)
    save_xls(metric_df, common_args, "Root Mean Squared Error")


@click.command(
    "lin-ccc",
    help="Compute Lin's Concordance Correlation Coefficient between a new rater and a ground truth built from trusted raters.",
)
@click.argument(
    "evaluated_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    callback=validate_input_file_type,
)
@click.pass_context
def ccc(ctx: click.Context, evaluated_file: Path):
    """Compare EVALUATED_FILE against the mean, minimum and maximum of the trusted input raters."""
    common_args: CommonArgs = ctx.obj
    eval_df = load_df(evaluated_file, common_args.id_attr)
    metric_df = compute_metric(
        evaluated_file.stem,
        lin_ccc,
        common_args.input_dfs,
        eval_df,
        common_args.target_attrs,
    )

    _print_metric_df(metric_df, "Lin CCC", evaluated_file)
    save_xls(metric_df, common_args, "Lin CCC")


@click.command(
    "icc",
    help="Compute ICC(1,1), ICC(2,1) and ICC(3,1) between a new rater and trusted raters.",
)
@click.argument(
    "evaluated_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    callback=validate_input_file_type,
)
@click.pass_context
def icc_cli(ctx: click.Context, evaluated_file: Path):
    """Compare EVALUATED_FILE as an additional rater against the trusted input raters."""
    common_args: CommonArgs = ctx.obj
    eval_df = load_df(evaluated_file, common_args.id_attr)
    metric_df = compute_many_metrics(
        evaluated_file.stem,
        {
            "ICC(1, 1)": (partial(icc, icc_type=ICCType.SingleMeasure), True),
            "ICC(2, 1)": (partial(icc, icc_type=ICCType.RandomK), True),
            "ICC(3, 1)": (partial(icc, icc_type=ICCType.FixedK), False),
        },
        dict(zip([x.stem for x in common_args.input_files], common_args.input_dfs)),
        eval_df,
        common_args.target_attrs,
    )
    _print_metric_df(metric_df, "Intra-Class Correlation", evaluated_file)
    save_xls(metric_df, common_args, "Intra-Class Correlation")
