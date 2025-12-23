import json
from pathlib import Path

import click
import pandas as pd
from datetime import datetime

from collections import Counter


def _assign_papers(paper_count: int, evaluators: int, eval_count: int):
    assert (
        eval_count <= evaluators
    ), "no point making more evaluations than available evaluators"

    total_performed_evals = paper_count * eval_count
    complete_cycles = total_performed_evals // evaluators
    remainder = total_performed_evals % evaluators

    # Build a cyclic sequence of people repeated r times
    people_seq = list(range(evaluators)) * complete_cycles

    # Partition into N consecutive blocks of eval_count size
    evaluations = [
        people_seq[j * eval_count:(j + 1) * eval_count]
        for j in range(paper_count)
    ]
    assert all(len(set(block)) == eval_count for block in evaluations)

    # - each person appears exactly r times
    c = Counter(p for block in evaluations for p in block)
    loads = [c[p] for p in range(evaluators)]
    assert all(x == complete_cycles for x in loads)

    return evaluations, loads


def _validate_evaluation_count(ctx: click.Context, param: click.Option, value: int) -> int:
    if param.name != "evaluation_count":
        return value
    evaluator_count = ctx.params.get("evaluator_count")
    if evaluator_count is None:
        # If limit is missing, let Click handle the required‑ness elsewhere.
        return value

    if not (0 < value <= evaluator_count):
        raise click.BadParameter(
            f"must be between 0 and {evaluator_count} (got {value})"
        )
    return value


@click.command("n-by-k-evals")
@click.argument(
    "selection",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True),
)
@click.option(
    "-n", "--evaluator-count",
    type=click.IntRange(min=1, max_open=True),
    help="number of evaluators to split the workload to"
)
@click.option(
    "-k", "--evaluation-count",
    type=int,
    callback=_validate_evaluation_count,
    help="number of times each paper must be evaluated by different evaluators: [1 .. evaluator count]",
)
@click.option(
    "-w", "--worksheet-name",
    type=str,
    help="name of the worksheet containing the studies to be evaluated",
)
@click.option(
    "-c", "--evaluation-criteria-config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True),
    required=False,
    help="path to a JSON config file containing evaluation criteria",
)
def n_by_k_evals(
    selection: str | Path,
    evaluator_count: int,
    evaluation_count: int,
    worksheet_name: str | None = None,
    eval_criteria_config: str | Path | None = None,
):
    with open("uploads/20250813-ersa-sms-selection.xlsx", "rb") as xls:
        df = pd.read_excel(xls, "Selection-Before-QA", engine="openpyxl", header=0)
    with open("uploads/ersa-sms-qa-config.json") as cfg:
        criteria_config = json.load(cfg)
    criteria = [x["label"] for x in criteria_config["criteria"]]
    evaluators = 5
    evaluations_per_paper = 3
    jobs, loads = _assign_papers(df.shape[0], evaluators, evaluations_per_paper)
    evaluator_papers = {evaluator_idx:[] for evaluator_idx in range(evaluators)}
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