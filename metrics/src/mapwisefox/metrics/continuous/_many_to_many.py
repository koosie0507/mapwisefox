from collections import defaultdict
from typing import Callable

import numpy as np
import pandas as pd


def _extract_rater_matrix(
    input_dfs: dict[str, pd.DataFrame], target_attr: str
) -> pd.DataFrame:
    values_dict = defaultdict(lambda: {k: 0 for k in input_dfs})
    for df_name, df in input_dfs.items():
        for row_id, row in df.iterrows():
            values_dict[row_id][df_name] = row[target_attr]

    rows = []
    for j in values_dict:
        arr = np.asarray(list(values_dict[j].values()), dtype=float)
        mask = arr != 0
        if len(arr[mask]) > 0:
            mean = arr[mask].mean()
            arr[~mask] = mean
        else:
            arr[:] = 1
        rows.append({"id": j, **{k: arr[i] for i, k in enumerate(input_dfs)}})

    return pd.DataFrame(rows).set_index("id", inplace=False)


def _compute_many_to_many_metric(
    metric: Callable,
    input_dfs: dict[str, pd.DataFrame],
    eval_df: pd.DataFrame,
    target_attr: str,
) -> float:
    raters_df = _extract_rater_matrix(input_dfs, target_attr)
    combined = raters_df.join(eval_df[[target_attr]], how="inner")
    n_by_k_matrix = combined.to_numpy()

    return round(metric(n_by_k_matrix), 4)


def compute_many_metrics(
    evaluator_name: str,
    metrics: dict[str, Callable],
    input_dfs: dict[str, pd.DataFrame],
    eval_df: pd.DataFrame,
    target_attrs: list[str],
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "evaluator": evaluator_name,
                "metric": m,
                **{
                    attr: _compute_many_to_many_metric(metric, input_dfs, eval_df, attr)
                    for attr in target_attrs
                },
            }
            for m, metric in metrics.items()
        ]
    )
