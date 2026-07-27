import numpy as np
import pandas as pd

from mapwisefox.metrics.continuous._one_to_one import compute_metric


def test_compute_metric_uses_mean_min_max():
    input_dfs = [
        pd.DataFrame({"score": [1.0, 2.0]}, index=["a", "b"]),
        pd.DataFrame({"score": [3.0, 4.0]}, index=["a", "b"]),
    ]
    eval_df = pd.DataFrame({"score": [2.0, 3.0]}, index=["a", "b"])

    result = compute_metric(
        "new_rater", lambda x, y: np.mean(np.abs(x - y)), input_dfs, eval_df, ["score"]
    )

    assert result["evaluator"].iloc[0] == "new_rater"
    assert set(result["ground truth"]) == {
        "average score",
        "minimum score",
        "maximum score",
    }


def test_compute_metric_missing_record_in_eval_uses_intersection():
    input_dfs = [
        pd.DataFrame({"score": [1.0, 2.0]}, index=["a", "b"]),
    ]
    eval_df = pd.DataFrame({"score": [1.0]}, index=["a"])

    result = compute_metric("rater", lambda x, y: 0.0, input_dfs, eval_df, ["score"])

    assert len(result) == 3
