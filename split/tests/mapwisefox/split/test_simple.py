"""Tests for simple non-overlapping workload splits."""

from pathlib import Path

import pandas as pd

from mapwisefox.split import run_command


def test_simple_writes_each_input_row_once(runner, workbook, tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    workbook(
        [
            {"cluster_id": "a", "title": "One"},
            {"cluster_id": "b", "title": "Two"},
            {"cluster_id": "c", "title": "Three"},
        ],
        name="input/papers-deduplicated-records.xlsx",
    )

    result = runner.invoke(run_command, ["simple", "-D", str(input_dir), "-n", "2"])

    assert result.exit_code == 0, result.output
    outputs = sorted(
        (input_dir / "splits" / "papers-deduplicated-records").glob("*.xlsx")
    )
    assert [path.name for path in outputs] == ["0001.xlsx", "0002.xlsx"]
    titles = [
        title
        for output in outputs
        for title in pd.read_excel(output, index_col="cluster_id")["title"].tolist()
    ]
    assert sorted(titles) == ["One", "Three", "Two"]


def test_simple_uses_custom_include_pattern(runner, workbook, tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    workbook([{"cluster_id": "a"}], name="input/custom.xlsx")

    result = runner.invoke(
        run_command,
        ["simple", "--input-dir", str(input_dir), "--include", "custom.xlsx"],
    )

    assert result.exit_code == 0, result.output
    assert (input_dir / "splits" / "custom" / "0001.xlsx").exists()


def test_simple_reports_when_no_input_matches(runner, tmp_path: Path):
    result = runner.invoke(run_command, ["simple", "--input-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert result.output == "done\n"


def test_simple_rejects_zero_split_count(runner, tmp_path: Path):
    result = runner.invoke(
        run_command, ["simple", "--input-dir", str(tmp_path), "--split-count", "0"]
    )

    assert result.exit_code == 2
    assert "0 is not in the range" in result.output


def test_simple_requires_cluster_id_column(runner, workbook, tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    workbook([{"title": "One"}], name="input/papers-deduplicated-records.xlsx")

    result = runner.invoke(run_command, ["simple", "--input-dir", str(input_dir)])

    assert result.exit_code == 1
    assert "cluster_id" in result.output
