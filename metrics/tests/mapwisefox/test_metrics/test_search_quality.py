import pandas as pd
import pytest
from click.testing import CliRunner

from mapwisefox.metrics._cli import metrics
from mapwisefox.metrics.search_quality import compute_search_quality


@pytest.fixture
def judgment_df():
    return pd.DataFrame(
        [
            {"doi": "10.1000/one", "title": "First paper", "year": 2024},
            {"doi": "", "title": "Second: Paper", "year": 2023},
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


def test_compute_search_quality_ignores_duplicate_records(
    judgment_df, search_results_df
):
    duplicate_results = pd.concat([search_results_df, search_results_df.iloc[[0]]])

    result = compute_search_quality(judgment_df, duplicate_results)

    assert result.precision == pytest.approx(2 / 3)


def test_compute_search_quality_returns_zero_for_empty_sets():
    result = compute_search_quality(pd.DataFrame(), pd.DataFrame())

    assert result.f1 == 0.0


def test_search_quality_command_prints_selected_metric(tmp_path):
    judgment_file = tmp_path / "judgment.csv"
    results_file = tmp_path / "results.csv"
    pd.DataFrame([{"doi": "10.1000/one", "title": "First", "year": 2024}]).to_csv(
        judgment_file, index=False
    )
    pd.DataFrame(
        [
            {"doi": "10.1000/one", "title": "First", "year": 2024},
            {"doi": "10.1000/two", "title": "Second", "year": 2024},
        ]
    ).to_csv(results_file, index=False)

    result = CliRunner().invoke(
        metrics,
        [
            "search-quality",
            "--metric",
            "jaccard",
            str(judgment_file),
            str(results_file),
        ],
    )

    assert result.exit_code == 0
    assert result.output == "judgment Jaccard: 50.00%\n"


def test_search_quality_command_handles_multiple_judgment_files(tmp_path):
    judgment_a = tmp_path / "judgment_a.csv"
    judgment_b = tmp_path / "judgment_b.csv"
    results_file = tmp_path / "results.csv"
    pd.DataFrame([{"doi": "10.1000/one", "title": "First", "year": 2024}]).to_csv(
        judgment_a, index=False
    )
    pd.DataFrame([{"doi": "10.1000/two", "title": "Second", "year": 2024}]).to_csv(
        judgment_b, index=False
    )
    pd.DataFrame(
        [
            {"doi": "10.1000/one", "title": "First", "year": 2024},
            {"doi": "10.1000/two", "title": "Second", "year": 2024},
        ]
    ).to_csv(results_file, index=False)

    result = CliRunner().invoke(
        metrics,
        [
            "search-quality",
            "--metric",
            "precision",
            str(judgment_a),
            str(judgment_b),
            str(results_file),
        ],
    )

    assert result.exit_code == 0
    assert "judgment_a Precision: 50.00%" in result.output
    assert "judgment_b Precision: 50.00%" in result.output


def test_search_quality_command_help_describes_the_metric_option():
    result = CliRunner().invoke(metrics, ["search-quality", "--help"])

    assert result.exit_code == 0
    assert "Order-independent metric to report." in result.output


def test_search_quality_command_writes_output_file(tmp_path):
    judgment_file = tmp_path / "judgment.csv"
    results_file = tmp_path / "results.csv"
    output_file = tmp_path / "output.xlsx"
    pd.DataFrame([{"doi": "10.1000/one", "title": "First", "year": 2024}]).to_csv(
        judgment_file, index=False
    )
    pd.DataFrame(
        [
            {"doi": "10.1000/one", "title": "First", "year": 2024},
            {"doi": "10.1000/two", "title": "Second", "year": 2024},
        ]
    ).to_csv(results_file, index=False)

    result = CliRunner().invoke(
        metrics,
        [
            "-o",
            str(output_file),
            "search-quality",
            "--metric",
            "jaccard",
            str(judgment_file),
            str(results_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()
    df = pd.read_excel(output_file, sheet_name="Search Quality")
    assert df["judgment_file"].iloc[0] == "judgment"
    assert df["metric"].iloc[0] == "jaccard"
    assert df["score"].iloc[0] == pytest.approx(0.5)
    assert df["precision"].iloc[0] == pytest.approx(0.5)
    assert df["recall"].iloc[0] == pytest.approx(1.0)
    assert df["f1"].iloc[0] == pytest.approx(2 / 3)
    assert df["jaccard"].iloc[0] == pytest.approx(0.5)
    assert df["dice"].iloc[0] == pytest.approx(2 / 3)
