import pandas as pd
import pytest
from click.testing import CliRunner

from mapwisefox.metrics._cli import metrics
from mapwisefox.metrics.information_retrieval._search_quality import (
    compute_search_quality,
)


@pytest.fixture
def judgment_df():
    return pd.DataFrame(
        [
            {"id": 1, "doi": "10.1000/one", "title": "First paper", "year": 2024},
            {"id": 2, "doi": "", "title": "Second: Paper", "year": 2023},
        ]
    )


@pytest.fixture
def search_results_df():
    return pd.DataFrame(
        [
            {"doi": "10.1000/one", "title": "Different title", "year": 2020},
            {"doi": "", "title": "Second Paper", "year": 2023},
            {"doi": "10.1000/extra", "title": "Extra paper", "year": 2024},
        ]
    )


@pytest.fixture
def csv_file(tmp_path, judgment_df):
    default_name = "judgment.csv"

    def _(file_name, records):
        df = pd.DataFrame(records) if records else judgment_df
        file_name = file_name or default_name
        file_path = tmp_path / file_name
        df.to_csv(file_path, index=False)
        return file_path

    return _


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        ("precision", 2 / 3),
        ("recall", 1.0),
        ("f1", 0.8),
        ("jaccard", 2 / 3),
        ("dice", 0.8),
    ],
)
def test_compute_search_quality_returns_selected_metric(
    judgment_df, search_results_df, metric, expected
):
    result = compute_search_quality(judgment_df, search_results_df)

    assert result.score(metric) == pytest.approx(expected)


def test_compute_search_quality_uses_custom_columns():
    judgment = pd.DataFrame(
        [
            {"custom_id": "A", "title": "ignored"},
            {"custom_id": "B", "title": "ignored"},
        ]
    )
    results = pd.DataFrame(
        [
            {"custom_id": "A", "title": "ignored"},
            {"custom_id": "C", "title": "ignored"},
        ]
    )

    result = compute_search_quality(judgment, results, columns=("custom_id",))

    assert result.precision == pytest.approx(0.5)
    assert result.recall == pytest.approx(0.5)


def test_compute_search_quality_ignores_duplicate_records(
    judgment_df, search_results_df
):
    duplicate_results = pd.concat([search_results_df, search_results_df.iloc[[0]]])

    result = compute_search_quality(judgment_df, duplicate_results)

    assert result.precision == pytest.approx(2 / 3)


def test_compute_search_quality_returns_zero_for_empty_sets():
    result = compute_search_quality(pd.DataFrame(), pd.DataFrame())

    assert result.f1 == 0.0


def test_search_quality_command_prints_all_metrics(tmp_path, csv_file):
    judgment_file = csv_file(
        "judgment.csv",
        [{"id": 1, "doi": "10.1000/one", "title": "First", "year": 2024}],
    )
    results_file = csv_file(
        "search_results.csv",
        [
            {"doi": "10.1000/one", "title": "First", "year": 2024},
            {"doi": "10.1000/two", "title": "Second", "year": 2024},
        ],
    )

    result = CliRunner().invoke(
        metrics,
        [
            "-i",
            str(judgment_file),
            "search-quality",
            str(results_file),
        ],
    )

    assert result.exit_code == 0
    assert "judgment (columns: doi):" in result.output
    assert "Precision:" in result.output and "50.00%" in result.output
    assert "Recall:" in result.output and "100.00%" in result.output
    assert "F1:" in result.output and "66.67%" in result.output
    assert "Jaccard:" in result.output and "50.00%" in result.output
    assert "Dice:" in result.output and "66.67%" in result.output


def test_search_quality_command_handles_multiple_judgment_files(tmp_path, csv_file):
    judgment_a = csv_file(
        "judgment_a.csv",
        [{"id": 1, "doi": "10.1000/one", "title": "First", "year": 2024}],
    )
    judgment_b = csv_file(
        "judgment_b.csv",
        [{"id": 2, "doi": "10.1000/two", "title": "Second", "year": 2024}],
    )
    results_file = csv_file(
        "results.csv",
        [
            {"doi": "10.1000/one", "title": "First", "year": 2024},
            {"doi": "10.1000/two", "title": "Second", "year": 2024},
        ],
    )

    result = CliRunner().invoke(
        metrics,
        [
            "-i",
            str(judgment_a),
            "-i",
            str(judgment_b),
            "search-quality",
            str(results_file),
        ],
    )

    assert result.exit_code == 0
    assert "judgment_a (columns: doi):" in result.output
    assert "judgment_b (columns: doi):" in result.output


def test_search_quality_command_uses_target_value_columns(tmp_path, csv_file):
    judgment_file = csv_file(
        "judgment.csv", [{"id": 1, "custom_id": "A"}, {"id": 2, "custom_id": "B"}]
    )
    results_file = csv_file("results.csv", [{"custom_id": "A"}, {"custom_id": "C"}])

    result = CliRunner().invoke(
        metrics,
        [
            "-t",
            "custom_id",
            "-i",
            str(judgment_file),
            "search-quality",
            str(results_file),
        ],
    )

    assert result.exit_code == 0
    assert "judgment (columns: custom_id):" in result.output
    assert "Precision:" in result.output and "50.00%" in result.output
    assert "Recall:" in result.output and "50.00%" in result.output


def test_search_quality_command_help_explains_input_file_usage():
    result = CliRunner().invoke(metrics, ["search-quality", "--help"])

    assert result.exit_code == 0
    assert (
        "Use -i/--input-file to specify judgment files containing lists of known good"
        in result.output
    )


def test_search_quality_command_writes_output_file(tmp_path, csv_file):
    judgment_file = csv_file(
        "judgment.csv",
        [{"id": 1, "doi": "10.1000/one", "title": "First", "year": 2024}],
    )
    results_file = csv_file(
        "results.csv",
        [
            {"doi": "10.1000/one", "title": "First", "year": 2024},
            {"doi": "10.1000/two", "title": "Second", "year": 2024},
        ],
    )
    output_file = tmp_path / "output.xlsx"
    result = CliRunner().invoke(
        metrics,
        [
            "-o",
            str(output_file),
            "-i",
            str(judgment_file),
            "search-quality",
            str(results_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()
    df = pd.read_excel(output_file, sheet_name="Search Quality")
    assert df["judgment_file"].iloc[0] == "judgment"
    assert df["columns"].iloc[0] == "doi"
    assert df["precision"].iloc[0] == pytest.approx(0.5)
    assert df["recall"].iloc[0] == pytest.approx(1.0)
    assert df["f1"].iloc[0] == pytest.approx(2 / 3)
    assert df["jaccard"].iloc[0] == pytest.approx(0.5)
    assert df["dice"].iloc[0] == pytest.approx(2 / 3)
