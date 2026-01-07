import click
import pandas as pd
from dataclasses import dataclass
from typing import TypedDict

from sklearn.metrics import cohen_kappa_score


DEFAULT_LABELS = ["include", "exclude"]
_RIGHT_SUFFIX = "_right"


@dataclass
class CmpSettings:
    dataframe: pd.DataFrame
    name: str
    label_col: str
    extra_output_cols: list[str]

    @property
    def label_values(self):
        return self.dataframe[self.label_col]


class KappaScoreRow(TypedDict):
    left: str
    right: str
    attribute: str
    score: float
    agreement: str
    diff_sheet_name: str


def _kappa_score(
    left: CmpSettings, right: CmpSettings, output_index_name: str, labels=None
):
    labels = labels or DEFAULT_LABELS
    disagreements_df = left.dataframe.join(
        right.dataframe, how="inner", rsuffix=_RIGHT_SUFFIX
    )
    right_label_col = f"{right.label_col}{_RIGHT_SUFFIX}"
    right_extra_cols = [
        f"{col_name}{_RIGHT_SUFFIX}" for col_name in right.extra_output_cols
    ]
    disagreements_df = disagreements_df[
        disagreements_df[left.label_col] != disagreements_df[right_label_col]
    ]
    output_columns = [
        left.label_col,
        right_label_col,
        *left.extra_output_cols,
        *right_extra_cols,
    ] + [
        col
        for col in left.dataframe.columns
        if col not in {left.label_col, *left.extra_output_cols}
    ]
    disagreements_df = (
        disagreements_df[output_columns]
        .rename(
            columns={
                left.label_col: f"{left.name}_decision",
                right_label_col: f"{right.name}_decision",
            }
        )
        .set_index(disagreements_df.index)
    )
    disagreements_df.index.set_names([output_index_name], inplace=True)

    kappa = cohen_kappa_score(left.label_values, right.label_values, labels=labels)

    return kappa, disagreements_df


def _compute_agreement(my_kappa):
    if my_kappa <= 0:
        return "chance agreement"
    elif my_kappa <= 0.29:
        return "poor agreement"
    elif my_kappa <= 0.40:
        return "fair agreement"
    elif my_kappa <= 0.60:
        return "moderate agreement"
    elif my_kappa <= 0.80:
        return "substantial agreement"
    else:
        return "almost perfect agreement"


def _print_kappa_score(decision_col, my_kappa, left_file_path, right_file_path):
    click.echo(
        f"The Cohen Kappa agreement score between {left_file_path.stem} and {right_file_path.stem} on {decision_col!r} is ",
        nl=False,
    )
    agreement = _compute_agreement(my_kappa)
    click.echo(click.style(f"{my_kappa:.2f}", bold=True), nl=False, color=True)
    click.echo(": [", nl=False)
    if my_kappa <= 0:
        click.echo(
            click.style(agreement, fg="white", bg="red", bold=True),
            nl=False,
            color=True,
        )
    elif my_kappa <= 0.29:
        click.echo(click.style(agreement, fg="red"), nl=False, color=True)
    elif my_kappa <= 0.40:
        click.echo(click.style(agreement, fg="yellow"), nl=False, color=True)
    elif my_kappa <= 0.60:
        click.echo(click.style(agreement, fg="cyan"), nl=False, color=True)
    elif my_kappa <= 0.80:
        click.echo(
            click.style(agreement, fg="green", bold=True),
            nl=False,
            color=True,
        )
    else:
        click.echo(
            click.style(agreement, fg="white", bg="green", bold=True),
            nl=False,
            color=True,
        )
    click.echo("]")


@click.command("kappa-score")
@click.pass_context
def kappa_score(ctx: click.Context):
    group_args = ctx.obj
    if len(group_args.input_files) != 2:
        raise click.BadOptionUsage(
            "input_files",
            "Cohen's Kappa score is a statistic which computes the agreement between exactly two raters. Please specify only two input files.",
            ctx,
        )

    left_file_path = group_args.input_files[0]
    right_file_path = group_args.input_files[1]

    stats = []

    disagreements = {}
    for decision_col in group_args.target_attrs:
        sheet_name = f"disagreements on {decision_col}"
        left_df = group_args.input_dfs[0][
            pd.notna(group_args.input_dfs[0][decision_col])
        ]
        right_df = group_args.input_dfs[1][
            pd.notna(group_args.input_dfs[1][decision_col])
        ]
        result_idx = left_df.index.intersection(right_df.index)
        left_df = left_df.loc[result_idx]
        right_df = right_df.loc[result_idx]
        left = CmpSettings(
            left_df,
            left_file_path.stem,
            decision_col,
            group_args.extra_cols,
        )
        right = CmpSettings(
            right_df,
            right_file_path.stem,
            decision_col,
            group_args.extra_cols,
        )

        my_kappa, disagreements_df = _kappa_score(left, right, group_args.id_attr)

        disagreements[sheet_name] = disagreements_df
        stats.append(
            KappaScoreRow(
                left=left_file_path.stem,
                right=right_file_path.stem,
                attribute=decision_col,
                score=my_kappa,
                agreement=_compute_agreement(my_kappa),
                diff_sheet_name=sheet_name,
            )
        )

        _print_kappa_score(decision_col, my_kappa, left_file_path, right_file_path)

    with pd.ExcelWriter(group_args.output_file, engine="openpyxl") as writer:
        pd.DataFrame(stats).to_excel(writer, sheet_name="stats", index=False)
        for sheet_name, df in disagreements.items():
            df.to_excel(writer, sheet_name=sheet_name, index=True)
