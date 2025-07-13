from pathlib import Path

import click
import pandas as pd
from sklearn.metrics import cohen_kappa_score

DEFAULT_LABELS = ["include", "exclude"]
_RIGHT_SUFFIX = "_right"


def _kappa_score(
    left_df,
    left_label_col,
    left_name,
    right_df,
    right_label_col,
    right_name,
    labels=None,
):
    labels = labels or DEFAULT_LABELS
    disagreements_df = left_df.join(right_df, how="inner", rsuffix=_RIGHT_SUFFIX)
    disagreements_df = disagreements_df[
        disagreements_df[left_label_col]
        != disagreements_df[f"{right_label_col}{_RIGHT_SUFFIX}"]
    ]
    output_columns = [left_label_col, f"{right_label_col}{_RIGHT_SUFFIX}"] + [
        col for col in left_df.columns if col != left_label_col
    ]
    disagreements_df = disagreements_df[output_columns].rename(
        columns={
            left_label_col: f"{left_name}_decision",
            f"{right_label_col}{_RIGHT_SUFFIX}": f"{right_name}_decision",
        }
    )

    kappa = cohen_kappa_score(
        left_df[left_label_col], right_df[right_label_col], labels=labels
    )

    return kappa, disagreements_df


@click.command()
@click.argument(
    "left_file_path",
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True
    ),
)
@click.option(
    "--left-id-column",
    "-l",
    default="cluster_id",
    type=click.STRING,
)
@click.option(
    "--left-decision-column",
    "-L",
    default="include",
    type=click.STRING,
)
@click.argument(
    "right_file_path",
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True
    ),
)
@click.option(
    "--right-id-column",
    "-r",
    default="cluster_id",
    type=click.STRING,
)
@click.option(
    "--right-decision-column",
    "-R",
    default="include",
    type=click.STRING,
)
@click.option(
    "--out-file-path",
    "-o",
    required=True,
    type=click.Path(dir_okay=False, file_okay=True, writable=True, resolve_path=True),
)
def main(
    left_file_path,
    left_id_column,
    left_decision_column,
    right_file_path,
    right_id_column,
    right_decision_column,
    out_file_path,
):
    left_file_path = Path(left_file_path)
    right_file_path = Path(right_file_path)
    left_df = pd.read_excel(left_file_path, index_col=left_id_column)
    left_df = left_df[pd.notna(left_df[left_decision_column])]
    right_df = pd.read_excel(right_file_path, index_col=right_id_column)
    right_df = right_df[pd.notna(right_df[right_decision_column])]
    result_idx = left_df.index.intersection(right_df.index)
    left_df = left_df.loc[result_idx]
    right_df = right_df.loc[result_idx]
    my_kappa, disagreements_df = _kappa_score(
        left_df,
        left_decision_column,
        left_file_path.stem,
        right_df,
        right_decision_column,
        right_file_path.stem,
    )
    disagreements_df.to_excel(out_file_path, index=False)
    _print_kappa_score(my_kappa, left_file_path, right_file_path)


def _print_kappa_score(my_kappa, left_file_path, right_file_path):
    click.echo(
        f"The Cohen Kappa agreement score between {left_file_path.stem} and {right_file_path.stem} is ",
        nl=False,
    )
    click.echo(click.style(f"{my_kappa:.2f}", bold=True), nl=False, color=True)
    click.echo(": [", nl=False)
    if my_kappa <= 0:
        click.echo(
            click.style("chance agreement", fg="white", bg="red", bold=True),
            nl=False,
            color=True,
        )
    elif my_kappa <= 0.29:
        click.echo(click.style("poor agreement", fg="red"), nl=False, color=True)
    elif my_kappa <= 0.40:
        click.echo(click.style("fair agreement", fg="orange"), nl=False, color=True)
    elif my_kappa <= 0.60:
        click.echo(click.style("moderate agreement", fg="gray"), nl=False, color=True)
    elif my_kappa <= 0.80:
        click.echo(
            click.style("substantial agreement", fg="green", bold=True),
            nl=False,
            color=True,
        )
    else:
        click.echo(
            click.style("almost perfect agreement", fg="white", bg="green", bold=True),
            nl=False,
            color=True,
        )
    click.echo("]")


if __name__ == "__main__":
    main()
