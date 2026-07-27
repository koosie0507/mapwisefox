"""Order-independent quality metrics for judged search results."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import click
import pandas as pd

from mapwisefox.metrics._types import CommonArgs
from mapwisefox.metrics._utils import load_df
from mapwisefox.metrics._validators import validate_input_file_type


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


def _comparison_value(record: pd.Series) -> str:
    doi = record.get("doi", "")
    if doi not in {"N/A", ""}:
        return doi.strip().lower()
    title = re.sub(
        r"(-|\s+)", "_", re.sub(r"[{}:-]", "", record["title"].strip().lower())
    )
    return f"{record['year']}_{title}"


def _comparison_values(dataframe: pd.DataFrame) -> set[str]:
    return set(dataframe.fillna("").apply(_comparison_value, axis=1))


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def compute_search_quality(
    judgment_df: pd.DataFrame, search_results_df: pd.DataFrame
) -> SearchQuality:
    """Compute order-independent precision, recall, F1, Jaccard, and Dice scores."""
    judgment_values = _comparison_values(judgment_df)
    search_result_values = _comparison_values(search_results_df)
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
            2 * true_positives, 2 * true_positives + false_positives + false_negatives
        ),
    )


@click.command(
    "search-quality", help="Measure a search result set against judgment files."
)
@click.option(
    "-m",
    "--metric",
    type=click.Choice(_METRIC_NAMES),
    default="f1",
    show_default=True,
    help="Order-independent metric to report.",
)
@click.argument(
    "judgment_files",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
    callback=validate_input_file_type,
)
@click.argument(
    "search_results_file",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
    callback=validate_input_file_type,
)
@click.pass_context
def search_quality(
    ctx: click.Context,
    judgment_files: list[Path],
    search_results_file: Path,
    metric: _MetricName,
) -> None:
    common_args: CommonArgs = ctx.obj
    results_df = load_df(search_results_file)
    rows = []
    for judgment_file in judgment_files:
        quality = compute_search_quality(load_df(judgment_file), results_df)
        score = quality.score(metric)
        click.echo(f"{judgment_file.stem} {metric.title()}: {score:.2%}")
        rows.append(
            {
                "judgment_file": judgment_file.stem,
                "metric": metric,
                "score": score,
                "precision": quality.precision,
                "recall": quality.recall,
                "f1": quality.f1,
                "jaccard": quality.jaccard,
                "dice": quality.dice,
            }
        )
    if common_args.output_file:
        df = pd.DataFrame(rows)
        with pd.ExcelWriter(
            common_args.output_file,
            if_sheet_exists="replace" if common_args.output_file.exists() else None,
            mode="a" if common_args.output_file.exists() else "w",
            engine="openpyxl",
        ) as writer:
            df.to_excel(writer, sheet_name="Search Quality", index=False)
