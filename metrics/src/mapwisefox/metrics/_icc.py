from enum import StrEnum

import numpy as np


class ICCType(StrEnum):
    SingleMeasure = "ICC1"  # targets rated by a different rater; random raters
    RandomK = "ICC2"  # random sample of K raters rate each target
    FixedK = "ICC3"  # fixed sample of K raters rate each target


def icc(data, icc_type: ICCType = ICCType.FixedK):
    """
    Compute ICC for a subjects x raters matrix `data`.
    icc_type: 'ICC1', 'ICC2', 'ICC3' — single-measure, absolute-agreement forms.
    Returns ICC float (may be negative).
    Formulas follow standard ANOVA mean-square decomposition【5】【6】.
    """
    a = np.asarray(data, dtype=float)
    if a.ndim != 2:
        raise ValueError("data must be 2D: subjects x raters")
    n, k = a.shape
    if n < 2 or k < 2:
        return np.nan

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

    it = icc_type.upper()
    if it == "ICC1":
        denom = msr + (k - 1) * mse
        return float((msr - mse) / denom) if denom != 0 else np.nan
    elif it == "ICC2":
        # two-way random, absolute agreement, single measure
        denom = msr + (k - 1) * mse + (k * (msc - mse) / n)
        return float((msr - mse) / denom) if denom != 0 else np.nan
    elif it == "ICC3":
        # two-way mixed, absolute agreement, single measure
        denom = msr + (k - 1) * mse
        return float((msr - mse) / denom) if denom != 0 else np.nan
    else:
        raise ValueError("icc_type must be one of 'ICC1','ICC2','ICC3'")
