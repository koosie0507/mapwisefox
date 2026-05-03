import math
import numpy as np


def lin_ccc(x: np.ndarray, y: np.ndarray) -> float:
    """Compute Lin's concordance correlation coefficient for two paired vectors.

    The shapes of ``x`` and ``y`` must be identical. Both parameters must be
    vectors.

    :param x: a 1D array with at least two elements
    :param y: a 1D array with at least two elements

    :return float: the value will be in the :math:[-1, 1] interval or
        ``float("nan")`` if the coefficient can't be computed
    :raises ValueError: ``x`` and ``y`` don't have the same shape.
    """
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
