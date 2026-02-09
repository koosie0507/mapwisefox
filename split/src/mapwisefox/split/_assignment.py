import json
from pathlib import Path
from typing import Any

import click
import pandas as pd
from datetime import datetime

from collections import Counter

from pandas import DataFrame


def _assign_papers(paper_count: int, evaluators: int, eval_count: int):
    assert (
        eval_count <= evaluators
    ), "no point making more evaluations than available evaluators"

    total_performed_evals = paper_count * eval_count
    complete_cycles = total_performed_evals // evaluators

    # Build a cyclic sequence of people repeated r times
    people_seq = list(range(evaluators)) * complete_cycles

    # Partition into N consecutive blocks of eval_count size
    evaluations = [
        people_seq[j * eval_count : (j + 1) * eval_count] for j in range(paper_count)
    ]
    assert all(len(set(block)) == eval_count for block in evaluations)

    # - each person appears exactly r times
    c = Counter(p for block in evaluations for p in block)
    loads = [c[p] for p in range(evaluators)]
    assert all(x == complete_cycles for x in loads)

    return evaluations, loads


def _validate_evaluation_count(
    ctx: click.Context, param: click.Option, value: int
) -> int:
    if param.name != "evaluation_count":
        return value
    evaluator_count = ctx.params.get("evaluator_count")
    if evaluator_count is None:
        # If limit is missing, let Click handle the required‑ness elsewhere.
        return value

    if not (0 < value <= evaluator_count):
        raise click.BadParameter(
            f"must be between 1 and {evaluator_count} (got {value})"
        )
    return value


def _init_eval_criteria(eval_criteria_config: str | Path | None) -> list[str]:
    criteria = ["study quality"]
    if eval_criteria_config is not None:
        with open(eval_criteria_config) as cfg:
            cfg_obj = json.load(cfg)
            criteria = [x["label"] for x in cfg_obj["criteria"]]
    return criteria


def _load_workload_df(
    selection: str | Path, worksheet_name: str | None
) -> (
    dict[Any, DataFrame] | dict[str, DataFrame] | dict[int | str, DataFrame] | DataFrame
):
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
    type=click.IntRange(min=1, max_open=True),
    help="number of evaluators to split the workload to",
)
@click.option(
    "-k",
    "--evaluation-count",
    type=int,
    callback=_validate_evaluation_count,
    help="number of times each paper must be evaluated by different evaluators: [1 .. evaluator count]",
)
@click.option(
    "-w",
    "--worksheet-name",
    type=str,
    help="name of the worksheet containing the studies to be evaluated",
)
@click.option(
    "-c",
    "--evaluation-criteria-config",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True
    ),
    required=False,
    help="path to a JSON config file containing evaluation criteria",
)
def n_by_k_evals(
    selection: str | Path,
    evaluator_count: int,
    evaluation_count: int,
    worksheet_name: str | None = None,
    evaluation_criteria_config: str | Path | None = None,
):
    df = _load_workload_df(selection, worksheet_name)
    criteria = _init_eval_criteria(evaluation_criteria_config)

    evaluators = evaluator_count
    evaluations_per_paper = evaluation_count

    jobs, loads = _assign_papers(df.shape[0], evaluators, evaluations_per_paper)
    evaluator_papers = {evaluator_idx: [] for evaluator_idx in range(evaluators)}
    for j, evaluator_ids in enumerate(jobs):
        for eid in evaluator_ids:
            row = df.iloc[j].to_dict()
            row.update({k: 0.0 for k in criteria})
            evaluator_papers[eid].append(row)
    evaluator_papers = {k: pd.DataFrame(v) for k, v in evaluator_papers.items()}
    for e, bundle in evaluator_papers.items():
        today = datetime.now().strftime("%Y%m%d")
        f = f"uploads/{today}-evaluator{e+1:02}.xlsx"
        print(f"saving papers for evaluator {e+1} to file {f}")
        bundle.to_excel(excel_writer=f, index=False, freeze_panes=(1, 5))


if __name__ == "__main__":
    n_by_k_evals()
