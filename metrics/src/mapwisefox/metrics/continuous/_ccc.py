import math
import numpy as np


def lin_ccc(x, y):
    """
    Lin's concordance correlation coefficient for two paired vectors.
    Returns float in [-1, 1]. Implementation follows Lin (1989).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape:
        raise ValueError("x and y must have same shape")
    n = x.size
    if n < 2:
        return np.nan

    mx = x.mean()
    my = y.mean()
    sx2 = x.var(ddof=1)
    sy2 = y.var(ddof=1)
    cov = np.cov(x, y, ddof=1)[0, 1]

    denom = sx2 + sy2 + (mx - my) ** 2
    if math.isclose(denom, 0.0):
        return np.nan
    ccc = (2 * cov) / denom
    return float(ccc)
