import re
from pathlib import Path

import click

from ._base import search_judge
from ._utils import load_df


@search_judge.command()
@click.argument(
    "judgment_file",
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True
    ),
    required=True,
)
@click.argument(
    "search_results_file",
    type=click.Path(
        exists=True, dir_okay=False, file_okay=True, readable=True, resolve_path=True
    ),
    required=True,
)
def quality(judgment_file, search_results_file) -> None:
    """Judge the quality of the search results against a judgment file.

    The judgment file must be crafted and supplied in advance. This quality
    verification technique originates in information retrieval where judgment
    files are often used in the context of tuning a search engine's signal/noise
    ratio.

    \b
    Args:
        judgment_file: file containing known good papers in either ``.bib``
            ``.csv`` or ``.xlsx`` format.
        search_results_file: file containing search results in ``.bib``,
            ``.csv`` or ``.xlsx`` format.
    Returns:
        precision, recall, f1 score
    """
    judgment_df = load_df(Path(judgment_file)).fillna(value="")
    search_results_df = load_df(Path(search_results_file)).fillna(value="")

    def _extract_str(record):
        if "doi" in record and record["doi"] not in {"N/A", ""}:
            return record["doi"].strip().lower()
        title_str = record["title"].strip().lower()
        title_str = re.sub(r"[{}:-]", "", title_str)
        title_str = re.sub(r"(-|\s+)", "_", title_str)
        year_str = str(record["year"])
        return f"{year_str}_{title_str}"

    judgment_df["compare_value"] = judgment_df.apply(_extract_str, axis=1)
    search_results_df["compare_value"] = search_results_df.apply(_extract_str, axis=1)

    tp_count = judgment_df.merge(
        search_results_df, on="compare_value", how="inner"
    ).shape[0]
    mismatch = judgment_df.merge(
        search_results_df, on="compare_value", how="outer", indicator=True
    )
    fp_count = mismatch[mismatch["_merge"] == "right_only"].shape[0]
    fn_count = mismatch[mismatch["_merge"] == "left_only"].shape[0]

    precision = tp_count / (tp_count + fp_count)
    recall = tp_count / (tp_count + fn_count)
    f1 = 2 * precision * recall / (precision + recall)

    click.echo(f"Precision: {click.style(f'{precision:.2%}', bold=True)}", color=True)
    click.echo(f"Recall:    {click.style(f'{recall:.2%}', bold=True)}", color=True)
    click.echo(f"F1 Score:  {click.style(f'{f1:.2%}', bold=True)}", color=True)
