from collections import defaultdict
from typing import Callable

import numpy as np
import pandas as pd


def _extract_ground_truth(
    input_dfs: list[pd.DataFrame], target_attr: str, stat: Callable
) -> pd.Series:
    values_dict = defaultdict(list)
    for df in input_dfs:
        for idx, row in df.iterrows():
            values_dict[idx].append(row[target_attr])
    stat_dict = {k: stat(v) for k, v in values_dict.items()}
    return pd.Series(stat_dict)


def _compute_one2one_metric(
    metric: Callable,
    input_dfs: list[pd.DataFrame],
    eval_df: pd.DataFrame,
    target_attr: str,
    value_stat: Callable,
) -> float:
    y_true = _extract_ground_truth(input_dfs, target_attr, value_stat)[eval_df.index]
    y_pred = eval_df[target_attr]

    return round(metric(y_true.to_numpy(), y_pred.to_numpy()), 4)


def compute_metric(
    evaluator_name: str,
    metric: Callable,
    input_dfs: list[pd.DataFrame],
    eval_df: pd.DataFrame,
    target_attrs: list[str],
) -> pd.DataFrame:
    value_stats = {
        "average score": np.mean,
        "minimum score": np.min,
        "maximum score": np.max,
    }
    return pd.DataFrame(
        [
            {
                "evaluator": evaluator_name,
                "ground truth": stat_label,
                **{
                    attr: _compute_one2one_metric(
                        metric, input_dfs, eval_df, attr, stat
                    )
                    for attr in target_attrs
                },
            }
            for stat_label, stat in value_stats.items()
        ]
    )
