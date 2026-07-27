import math
import numpy as np


def lin_ccc(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape:
        raise ValueError("x and y must have same shape")

    n = x.size
    if n < 2:
        return float("nan")

    mx = x.mean()
    my = y.mean()
    sx2 = x.var(ddof=1)
    sy2 = y.var(ddof=1)
    cov = np.cov(x, y, ddof=1)[0, 1]

    D = sx2 + sy2 + (mx - my) ** 2
    if math.isclose(D, 0.0):
        return float("nan")

    ccc = (2 * cov) / D
    return round(ccc, 4)
