from collections import defaultdict
from functools import partial
from typing import Callable

import numpy as np
import pandas as pd


def _extract_random_ratings(
    input_dfs: dict[str, pd.DataFrame], target_attr: str
) -> pd.DataFrame:
    values_dict = defaultdict(list)
    for df_name, df in input_dfs.items():
        for row_id, row in df.iterrows():
            values_dict[row_id].append(row[target_attr])

    k = min(map(len, values_dict.values()))
    rng = np.random.default_rng()
    ratings = [
        {
            "id": row_id,
            **{
                f"rater_{i}": rating
                for i, rating in enumerate(
                    rng.choice(
                        np.asarray(row_ratings, dtype=np.float32), size=k, replace=False
                    )
                )
            },
        }
        for row_id, row_ratings in values_dict.items()
    ]
    return pd.DataFrame(ratings).set_index("id", inplace=False)


def _extract_fixed_ratings(
    input_dfs: dict[str, pd.DataFrame],
    target_attr: str,
) -> pd.DataFrame:
    df_index = {df_name: i for i, df_name in enumerate(input_dfs)}
    values_dict = defaultdict(partial(np.zeros, len(input_dfs), dtype=np.float32))

    for df_name, df in input_dfs.items():
        for row_id, row in df.iterrows():
            j = df_index[df_name]
            values_dict[row_id][j] = row[target_attr]

    def _fill_zeros_with_average(arr):
        mask = arr != 0
        if len(arr[mask]) == 0:
            return arr
        mean = arr[mask].mean()
        arr[~mask] = mean
        return arr

    rows = [
        {
            "id": row_id,
            **{
                f"rater_{i}": r
                for i, r in enumerate(_fill_zeros_with_average(row_ratings))
            },
        }
        for row_id, row_ratings in values_dict.items()
    ]
    return pd.DataFrame(rows).set_index("id", inplace=False)


def _compute_many_to_many_metric(
    metric: Callable,
    input_dfs: dict[str, pd.DataFrame],
    eval_df: pd.DataFrame,
    target_attr: str,
    allow_random: bool,
) -> float:
    raters_df = (
        _extract_random_ratings(input_dfs, target_attr)
        if allow_random
        else _extract_fixed_ratings(input_dfs, target_attr)
    )
    combined = raters_df.join(eval_df[[target_attr]], how="inner")
    n_by_k_matrix = combined.to_numpy()

    return round(metric(n_by_k_matrix), 4)


def compute_many_metrics(
    evaluator_name: str,
    metrics: dict[str, tuple[Callable, bool]],
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
                    attr: _compute_many_to_many_metric(
                        metric, input_dfs, eval_df, attr, allow_random
                    )
                    for attr in target_attrs
                },
            }
            for m, (metric, allow_random) in metrics.items()
        ]
    )
