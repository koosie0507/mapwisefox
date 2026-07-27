"""Order-independent quality metrics for search results using human judgment files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import click
import pandas as pd

from mapwisefox.metrics._types import CommonArgs
from mapwisefox.metrics._utils import load_df
from mapwisefox.metrics._validators import validate_input_file_type

_DEFAULT_COMPARISON_COLUMNS: tuple[str, ...] = ("doi",)
_MetricName = Literal["precision", "recall", "f1", "jaccard", "dice"]
_METRIC_NAMES: tuple[_MetricName, ...] = (
    "precision",
    "recall",
    "f1",
    "jaccard",
    "dice",
)


@dataclass(frozen=True)
class SearchQuality:
    """Set-based quality scores for a judged search result set."""

    precision: float
    recall: float
    f1: float
    jaccard: float
    dice: float

    def score(self, metric: _MetricName) -> float:
        """Return the score identified by ``metric``."""
        return {
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "jaccard": self.jaccard,
            "dice": self.dice,
        }[metric]


def _comparison_value(record: pd.Series, columns: tuple[str, ...]) -> str:
    return "_".join(str(record.get(col, "")).strip().lower() for col in columns)


def _comparison_values(dataframe: pd.DataFrame, columns: tuple[str, ...]) -> set[str]:
    return set(dataframe.fillna("").apply(_comparison_value, axis=1, args=(columns,)))


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def compute_search_quality(
    judgment_df: pd.DataFrame,
    search_results_df: pd.DataFrame,
    columns: tuple[str, ...] = _DEFAULT_COMPARISON_COLUMNS,
) -> SearchQuality:
    """Compute order-independent precision, recall, F1, Jaccard, and Dice scores."""
    judgment_values = _comparison_values(judgment_df, columns)
    search_result_values = _comparison_values(search_results_df, columns)
    true_positives = len(judgment_values & search_result_values)
    false_positives = len(search_result_values - judgment_values)
    false_negatives = len(judgment_values - search_result_values)
    precision = _ratio(true_positives, true_positives + false_positives)
    recall = _ratio(true_positives, true_positives + false_negatives)
    return SearchQuality(
        precision=precision,
        recall=recall,
        f1=_ratio(2 * precision * recall, precision + recall),
        jaccard=_ratio(
            true_positives, true_positives + false_positives + false_negatives
        ),
        dice=_ratio(
            2 * true_positives,
            2 * true_positives + false_positives + false_negatives,
        ),
    )


@click.command(
    "search-quality",
    help=r"""Measure search results against known-good search results.
    
    Allows checking how well a search query retrieves papers that should be a
    part of the systematic literature review.
    
    Use -i/--input-file to specify judgment files containing lists of known good
    papers. More than one such judgments may be used. The judgment files must
    define a column that acts as a primary key. This column must not coincide
    with the column(s) used to compare known-good records with the records
    retrieved via search. The default comparison column is "doi". The comparison
    columns must be present in both the judgment file and the search results.""",
)
@click.argument(
    "search_results_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
    callback=validate_input_file_type,
)
@click.pass_context
def search_quality(ctx: click.Context, search_results_file: Path) -> None:
    obj = ctx.ensure_object(CommonArgs)
    columns = tuple(obj.target_attrs) or _DEFAULT_COMPARISON_COLUMNS
    columns_label = "; ".join(columns)
    results_df = load_df(search_results_file)
    rows = []
    for judgment_path, judgment_df in zip(obj.input_files, obj.input_dfs):
        quality = compute_search_quality(judgment_df, results_df, columns=columns)
        click.echo(f"{judgment_path.stem} (columns: {columns_label}):")
        click.echo(f"  Precision: {quality.precision:.2%}")
        click.echo(f"  Recall:    {quality.recall:.2%}")
        click.echo(f"  F1:        {quality.f1:.2%}")
        click.echo(f"  Jaccard:   {quality.jaccard:.2%}")
        click.echo(f"  Dice:      {quality.dice:.2%}")
        if not obj.output_file:
            continue
        rows.append(
            {
                "judgment_file": judgment_path.stem,
                "columns": columns_label,
                "precision": quality.precision,
                "recall": quality.recall,
                "f1": quality.f1,
                "jaccard": quality.jaccard,
                "dice": quality.dice,
            }
        )
    if not obj.output_file:
        return

    output_metrics_df = pd.DataFrame(rows)
    with pd.ExcelWriter(
        obj.output_file,
        if_sheet_exists="replace" if obj.output_file.exists() else None,
        mode="a" if obj.output_file.exists() else "w",
        engine="openpyxl",
    ) as writer:
        output_metrics_df.to_excel(writer, sheet_name="Search Quality", index=False)
