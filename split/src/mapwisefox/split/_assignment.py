from collections import Counter
from datetime import datetime
import json
from pathlib import Path

import click
import pandas as pd
from pandas import DataFrame


def _assign_papers(
    paper_count: int, evaluators: int, eval_count: int
) -> tuple[list[list[int]], list[int]]:
    total_evaluations = paper_count * eval_count
    cycles = (total_evaluations + evaluators - 1) // evaluators
    people_sequence = (list(range(evaluators)) * cycles)[:total_evaluations]
    evaluations = [
        people_sequence[index * eval_count : (index + 1) * eval_count]
        for index in range(paper_count)
    ]
    counts = Counter(
        evaluator for evaluation in evaluations for evaluator in evaluation
    )
    loads = [counts[evaluator] for evaluator in range(evaluators)]
    return evaluations, loads


def _init_additional_cols(eval_criteria_config: str | Path | None) -> list[str]:
    criteria = []
    if eval_criteria_config is not None:
        with open(eval_criteria_config) as cfg:
            cfg_obj = json.load(cfg)
            criteria = [x["label"] for x in cfg_obj["criteria"]]
    return criteria


def _load_workload_df(selection: str | Path, worksheet_name: str | None) -> DataFrame:
    with open(selection, "rb") as xls:
        kwargs = dict(engine="openpyxl", header=0)
        if worksheet_name is not None:
            kwargs.update(dict(sheet_name=worksheet_name))
        df = pd.read_excel(xls, **kwargs)
    return df


@click.command("for-evaluation")
@click.argument(
    "selection",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True
    ),
)
@click.option(
    "-n",
    "--evaluator-count",
    type=click.IntRange(min=1),
    required=True,
    help="Number of reviewers receiving assigned studies.",
)
@click.option(
    "-k",
    "--evaluation-count",
    type=click.IntRange(min=1),
    required=True,
    help="Number of distinct reviewers assigned to each study.",
)
@click.option(
    "-w",
    "--worksheet-name",
    type=str,
    help="Name of the worksheet containing the studies to be evaluated.",
)
@click.option(
    "-c",
    "--evaluation-criteria-config",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True
    ),
    help="Assistant Study QA criteria JSON file whose labels become score columns.",
)
def n_by_k_evals(
    selection: str | Path,
    evaluator_count: int,
    evaluation_count: int,
    worksheet_name: str | None = None,
    evaluation_criteria_config: str | Path | None = None,
) -> None:
    """Assign each study to a requested number of distinct reviewers."""
    if evaluation_count > evaluator_count:
        raise click.BadParameter(
            f"must be between 1 and {evaluator_count} (got {evaluation_count})",
            param_hint="--evaluation-count",
        )
    selection = Path(selection)
    df = _load_workload_df(selection, worksheet_name)
    criteria = _init_additional_cols(evaluation_criteria_config)

    jobs, _ = _assign_papers(df.shape[0], evaluator_count, evaluation_count)
    evaluator_papers = {evaluator_idx: [] for evaluator_idx in range(evaluator_count)}
    for j, evaluator_ids in enumerate(jobs):
        for eid in evaluator_ids:
            row = df.iloc[j].to_dict()
            row.update({k: 0.0 for k in criteria})
            evaluator_papers[eid].append(row)
    evaluator_papers = {k: pd.DataFrame(v) for k, v in evaluator_papers.items()}

    for e, bundle in evaluator_papers.items():
        today = datetime.now().strftime("%Y%m%d")
        f = f"{selection.parent}/{today}-evaluator{e+1:02}.xlsx"
        print(f"saving papers for evaluator {e+1} to file {f}")
        bundle.to_excel(excel_writer=f, index=False)


if __name__ == "__main__":
    n_by_k_evals()
