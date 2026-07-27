import pandas as pd
import pytest
from click.testing import CliRunner

from mapwisefox.metrics._cli import metrics
from mapwisefox.metrics.categorical._cli import (
    CmpSettings,
    _compute_agreement,
    _kappa_score,
)


@pytest.fixture
def rater_df():
    return pd.DataFrame(
        {
            "decision": ["include", "exclude", "include", "include"],
            "title": ["A", "B", "C", "D"],
        },
        index=["1", "2", "3", "4"],
    )


@pytest.fixture
def other_rater_df():
    return pd.DataFrame(
        {
            "decision": ["include", "include", "include", "exclude"],
            "title": ["A", "B", "C", "D"],
        },
        index=["1", "2", "3", "4"],
    )


@pytest.mark.parametrize(
    "score,label",
    [
        (-0.1, "chance agreement"),
        (0.0, "chance agreement"),
        (0.20, "poor agreement"),
        (0.35, "fair agreement"),
        (0.50, "moderate agreement"),
        (0.70, "substantial agreement"),
        (0.81, "almost perfect agreement"),
        (1.0, "almost perfect agreement"),
    ],
)
def test_compute_agreement(score, label):
    assert _compute_agreement(score) == label


def test_kappa_score_command_requires_two_files(csv_file):
    result = CliRunner().invoke(
        metrics,
        [
            "-i",
            str(csv_file([{"id": "1", "decision": "include"}])),
            "-t",
            "decision",
            "kappa-score",
        ],
    )
    assert result.exit_code != 0
    assert "exactly two raters" in result.output


def test_kappa_score_command_prints_score_and_writes_output(
    tmp_path, csv_file, rater_df, other_rater_df
):
    left = csv_file(
        [
            {"id": idx, "decision": row["decision"], "title": row["title"]}
            for idx, row in rater_df.iterrows()
        ],
        "left.csv",
    )
    right = csv_file(
        [
            {"id": idx, "decision": row["decision"], "title": row["title"]}
            for idx, row in other_rater_df.iterrows()
        ],
        "right.csv",
    )
    output = tmp_path / "kappa.xlsx"
    result = CliRunner().invoke(
        metrics,
        [
            "-i",
            str(left),
            "-i",
            str(right),
            "-t",
            "decision",
            "-o",
            str(output),
            "kappa-score",
        ],
    )
    assert result.exit_code == 0
    assert "Cohen Kappa agreement score" in result.output
    assert output.exists()


def test_kappa_score_command_custom_labels(tmp_path, csv_file):
    left = csv_file([{"id": "1", "vote": "yes"}, {"id": "2", "vote": "no"}], "left.csv")
    right = csv_file(
        [{"id": "1", "vote": "yes"}, {"id": "2", "vote": "yes"}], "right.csv"
    )
    result = CliRunner().invoke(
        metrics,
        [
            "-i",
            str(left),
            "-i",
            str(right),
            "-t",
            "vote",
            "kappa-score",
            "--agreement-labels",
            "yes,no",
        ],
    )
    assert result.exit_code == 0
    assert "Cohen Kappa agreement score" in result.output


def test_kappa_score_excludes_missing_decisions():
    left = pd.DataFrame({"d": ["include", "exclude", "exclude"]}, index=["1", "2", "3"])
    right = pd.DataFrame(
        {"d": ["include", "exclude", "exclude"]}, index=["1", "2", "3"]
    )

    score, _ = _kappa_score(
        CmpSettings(left, "L", "d", []),
        CmpSettings(right, "R", "d", []),
        "id",
    )
    assert score == pytest.approx(1.0)


def test_kappa_score_without_output_does_not_crash(
    tmp_path, csv_file, rater_df, other_rater_df
):
    left = csv_file(
        [
            {"id": idx, "decision": row["decision"], "title": row["title"]}
            for idx, row in rater_df.iterrows()
        ],
        "left.csv",
    )
    right = csv_file(
        [
            {"id": idx, "decision": row["decision"], "title": row["title"]}
            for idx, row in other_rater_df.iterrows()
        ],
        "right.csv",
    )
    result = CliRunner().invoke(
        metrics,
        [
            "-i",
            str(left),
            "-i",
            str(right),
            "-t",
            "decision",
            "kappa-score",
        ],
    )
    assert result.exit_code == 0
    assert "Cohen Kappa agreement score" in result.output
