import math

import numpy as np
import pytest

from mapwisefox.metrics.continuous._ccc import lin_ccc


@pytest.mark.parametrize(
    "x,y,expected",
    [
        ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], 1),
        ([1, 2, 3, 4, 5], [5, 4, 3, 2, 1], -1),
        ([1, 2, 3, 4, 5], [1.1, 1.9, 3.2, 3.8, 5.1], 0.9945),
    ],
)
def test_basic_cases(x, y, expected):
    actual = lin_ccc(np.asarray(x), np.asarray(y))
    assert math.isclose(actual, expected)


def test_offset_penalty():
    x = np.asarray([1, 2, 3, 4, 5])
    y = np.asarray([11, 12, 13, 14, 15])
    C = np.corrcoef(x, y)
    pearson = C[0, 1].item()
    actual = lin_ccc(x, y)

    assert 0 <= actual < pearson
    assert pearson - actual > 0.9


def test_close_variance():
    x = np.asarray([1, 2, 3, 4, 5])
    y = np.asarray([1, 2, 2, 4, 6])
    C = np.corrcoef(x, y)
    pearson = C[0, 1].item()
    actual = lin_ccc(x, y)

    assert pearson > actual > 0
    assert pearson - actual < 0.05


def test_scale_distorsion():
    x = np.asarray([1, 2, 3, 4, 5])
    y = np.asarray([2, 4, 6, 8, 10])
    C = np.corrcoef(x, y)
    pearson = C[0, 1].item()
    actual = lin_ccc(x, y)

    assert pearson > actual > 0
    assert pearson - actual > 0.5


def test_single_element():
    x = np.asarray([1])
    assert math.isnan(lin_ccc(x, x))


def test_symmetry():
    x = np.asarray([1, 2, 3, 4, 5])
    y = np.asarray([2, 4, 6, 8, 10])

    assert lin_ccc(x, y) == lin_ccc(y, x)


def test_sign_flip():
    x = np.asarray([1, 2, 3, 4, 5])
    y = np.asarray([2, 4, 6, 8, 10])

    assert lin_ccc(x, y) == lin_ccc(-x, -y)


def test_translation():
    x = np.asarray([1, 2, 3, 4, 5])
    y = np.asarray([2, 4, 6, 8, 10])
    c = np.asarray([1] * 5)

    assert lin_ccc(x, y) == lin_ccc(x + c, y + c)


def test_scale():
    x = np.asarray([1, 2, 3, 4, 5])
    y = np.asarray([2, 4, 6, 8, 10])
    a = np.asarray([4] * 5)

    assert lin_ccc(x, y) == lin_ccc(a * x, a * y)


def test_zero_variance():
    x = np.asarray([1, 1, 1, 1, 1])
    y = np.asarray([1, 1, 1, 1, 1])

    assert math.isnan(lin_ccc(x, y))


def test_one_constant():
    x = np.asarray([1, 2, 3])
    y = np.asarray([2, 2, 2])

    assert lin_ccc(x, y) == 0.0
