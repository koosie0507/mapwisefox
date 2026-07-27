import pandas as pd
import pytest

from mapwisefox.metrics.continuous._many_to_many import (
    _extract_random_ratings,
    _extract_fixed_ratings,
    compute_many_metrics,
)


def test_extract_random_ratings_downsamples_to_minimum_count():
    input_dfs = {
        "r1": pd.DataFrame({"score": [1.0, 2.0]}, index=["a", "b"]),
        "r2": pd.DataFrame({"score": [1.5]}, index=["a"]),
    }
    result = _extract_random_ratings(input_dfs, "score")

    # Records with ratings: a and b; k=1 rater column per record.
    assert result.shape == (2, 1)


def test_extract_fixed_ratings_fills_missing_with_row_average():
    input_dfs = {
        "r1": pd.DataFrame({"score": [1.0, 2.0]}, index=["a", "b"]),
        "r2": pd.DataFrame({"score": [3.0]}, index=["a"]),
    }
    result = _extract_fixed_ratings(input_dfs, "score")

    assert result.loc["a", "rater_0"] == pytest.approx(1.0)
    assert result.loc["a", "rater_1"] == pytest.approx(3.0)
    # r2 did not rate b, so its value is imputed from b's observed average.
    assert result.loc["b", "rater_1"] == pytest.approx(2.0)


def test_extract_fixed_ratings_all_zeros_returns_zero_row():
    input_dfs = {
        "r1": pd.DataFrame({"score": [0.0]}, index=["a"]),
        "r2": pd.DataFrame({"score": [0.0]}, index=["a"]),
    }
    result = _extract_fixed_ratings(input_dfs, "score")

    assert (result.loc["a"].to_numpy() == 0).all()


def test_compute_many_metrics_runs_for_all_variants(tmp_path):
    input_dfs = {
        "r1": pd.DataFrame({"score": [1.0, 2.0]}, index=["a", "b"]),
        "r2": pd.DataFrame({"score": [1.1, 2.1]}, index=["a", "b"]),
    }
    eval_df = pd.DataFrame({"score": [1.0, 2.0]}, index=["a", "b"])

    def dummy_metric(matrix):
        return 0.5

    result = compute_many_metrics(
        "new",
        {"m1": (dummy_metric, True), "m2": (dummy_metric, False)},
        input_dfs,
        eval_df,
        ["score"],
    )

    assert len(result) == 2
    assert result["score"].iloc[0] == 0.5
