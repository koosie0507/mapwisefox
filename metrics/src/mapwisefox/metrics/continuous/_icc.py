from enum import StrEnum

import numpy as np


class ICCType(StrEnum):
    SingleMeasure = "ICC1"  # targets rated by a different rater; random raters
    RandomK = "ICC2"  # random sample of K raters rate each target
    FixedK = "ICC3"  # fixed sample of K raters rate each target


def __icc_1(a: np.ndarray):
    n, k = a.shape
    grand_mean = a.mean()
    mean_subj = a.mean(axis=1)

    ss_between = k * np.sum((mean_subj - grand_mean) ** 2)
    ss_within = np.sum((a - mean_subj[:, None]) ** 2)

    ms_between = ss_between / (n - 1)
    ms_within = ss_within / (n * (k - 1))

    denominator = ms_between + (k - 1) * ms_within
    if denominator == 0:
        return float("nan")
    return round((ms_between - ms_within) / denominator, 4)


def icc(data: np.ndarray, icc_type: ICCType = ICCType.FixedK) -> float:
    """Compute the intra-class correlation coefficient for n subjects by k raters."""

    a = np.asarray(data, dtype=float)
    if a.ndim != 2:
        raise ValueError("data must be 2D: subjects x raters")
    n, k = a.shape
    if n < 2 or k < 2:
        return float("nan")

    if icc_type == ICCType.SingleMeasure:
        return __icc_1(a)

    grand_mean = a.mean()
    mean_subj = a.mean(axis=1)  # shape (n,)
    mean_rater = a.mean(axis=0)  # shape (k,)

    ss_total = np.sum((a - grand_mean) ** 2)
    ss_rows = k * np.sum((mean_subj - grand_mean) ** 2)
    ss_cols = n * np.sum((mean_rater - grand_mean) ** 2)
    ss_error = ss_total - ss_rows - ss_cols

    msr = ss_rows / (n - 1)  # between subjects
    msc = ss_cols / (k - 1)  # between raters
    mse = ss_error / ((n - 1) * (k - 1))  # residual

    denominator = 0
    match icc_type:
        case ICCType.RandomK:
            denominator = msr + (k - 1) * mse + (k * (msc - mse) / n)
        case ICCType.FixedK:
            denominator = msr + (k - 1) * mse
        case _:
            raise ValueError(f"icc_type must be one of {', '.join(ICCType)}")

    if denominator == 0:
        return float("nan")

    return round((msr - mse) / denominator, 4)
