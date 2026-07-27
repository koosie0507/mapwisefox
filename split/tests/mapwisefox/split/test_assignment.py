"""Tests for multi-rater workload assignments."""

from collections import Counter
from pathlib import Path

import pandas as pd

from mapwisefox.split import run_command
from mapwisefox.split._assignment import (
    _assign_papers,
    _init_additional_cols,
    _load_workload_df,
)


def test_assign_papers_balances_an_uneven_workload():
    assignments, loads = _assign_papers(paper_count=5, evaluators=3, eval_count=2)

    assert all(len(assignees) == len(set(assignees)) == 2 for assignees in assignments)
    assert sum(loads) == 10
    assert max(loads) - min(loads) == 1


def test_assign_papers_handles_no_papers():
    assert _assign_papers(paper_count=0, evaluators=2, eval_count=1) == ([], [0, 0])


def test_init_additional_cols_reads_criteria_labels(criteria_config: Path):
    assert _init_additional_cols(criteria_config) == [
        "clear_objectives",
        "appropriate_design",
    ]


def test_init_additional_cols_returns_empty_list_without_config():
    assert _init_additional_cols(None) == []


def test_load_workload_df_reads_named_worksheet(workbook):
    source = workbook([{"title": "Ignored"}], sheet="First")
    with pd.ExcelWriter(source, engine="openpyxl", mode="a") as writer:
        pd.DataFrame([{"title": "Selected"}]).to_excel(
            writer, sheet_name="Selected", index=False
        )

    dataframe = _load_workload_df(source, "Selected")

    assert dataframe["title"].tolist() == ["Selected"]


def test_load_workload_df_reads_first_worksheet_by_default(workbook):
    source = workbook([{"title": "First"}])

    dataframe = _load_workload_df(source, None)

    assert dataframe["title"].tolist() == ["First"]


def test_for_evaluation_writes_assignments_and_criteria(
    monkeypatch, runner, workbook, criteria_config: Path
):
    source = workbook(
        [{"study_id": number, "title": f"Study {number}"} for number in range(5)]
    )
    monkeypatch.setattr("mapwisefox.split._assignment.datetime", FixedDateTime)

    result = runner.invoke(
        run_command,
        [
            "for-evaluation",
            str(source),
            "--evaluator-count",
            "3",
            "--evaluation-count",
            "2",
            "--evaluation-criteria-config",
            str(criteria_config),
            "--worksheet-name",
            "Studies",
        ],
    )

    assert result.exit_code == 0, result.output
    outputs = sorted(source.parent.glob("20260102-evaluator*.xlsx"))
    assert [path.name for path in outputs] == [
        "20260102-evaluator01.xlsx",
        "20260102-evaluator02.xlsx",
        "20260102-evaluator03.xlsx",
    ]
    assignments = [pd.read_excel(path) for path in outputs]
    received = Counter(
        study_id for assignment in assignments for study_id in assignment["study_id"]
    )
    assert received == Counter({number: 2 for number in range(5)})
    assert {len(assignment) for assignment in assignments} == {3, 4}
    assert all(
        assignment[["clear_objectives", "appropriate_design"]].eq(0.0).all().all()
        for assignment in assignments
    )


def test_for_evaluation_requires_evaluator_count(runner, workbook):
    result = runner.invoke(
        run_command, ["for-evaluation", str(workbook([])), "-k", "1"]
    )

    assert result.exit_code == 2
    assert "--evaluator-count" in result.output


def test_for_evaluation_rejects_too_many_evaluations(runner, workbook):
    result = runner.invoke(
        run_command,
        ["for-evaluation", str(workbook([])), "-n", "2", "-k", "3"],
    )

    assert result.exit_code == 2
    assert "must be between 1 and 2" in result.output


class FixedDateTime:
    """Minimal datetime replacement for deterministic output paths."""

    @classmethod
    def now(cls):
        return cls()

    def strftime(self, format_string: str) -> str:
        return "20260102"
