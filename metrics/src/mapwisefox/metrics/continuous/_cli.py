from functools import partial
from pathlib import Path

import click
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from mapwisefox.metrics._types import CommonArgs
from mapwisefox.metrics._utils import load_df
from mapwisefox.metrics._validators import validate_input_file_type
from mapwisefox.metrics.continuous._ccc import lin_ccc
from mapwisefox.metrics.continuous._cli_util import save_xls
from mapwisefox.metrics.continuous._icc import icc, ICCType
from mapwisefox.metrics.continuous._many_to_many import compute_many_metrics
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

    save_xls(metric_df, common_args, "Mean Absolute Error")


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

    save_xls(metric_df, common_args, "Root Mean Squared Error")


@click.command("lin-ccc")
@click.argument(
    "evaluated_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    callback=validate_input_file_type,
)
@click.pass_context
def ccc(ctx: click.Context, evaluated_file: Path):
    common_args: CommonArgs = ctx.obj
    eval_df = load_df(evaluated_file, common_args.id_attr)
    metric_df = compute_metric(
        evaluated_file.stem,
        lin_ccc,
        common_args.input_dfs,
        eval_df,
        common_args.target_attrs,
    )

    save_xls(metric_df, common_args, "Lin Concordance Correlation Coefficient")


@click.command("icc")
@click.argument(
    "evaluated_file",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
    callback=validate_input_file_type,
)
@click.pass_context
def icc_cli(ctx: click.Context, evaluated_file: Path):
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
    save_xls(metric_df, common_args, "Intra-Class Correlation")
