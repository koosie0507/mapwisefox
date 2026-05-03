import math

import numpy as np
import pytest

from mapwisefox.metrics.continuous._icc import icc, ICCType


@pytest.fixture
def example_4x6():
    return np.array(
        [
            [9, 2, 5, 8],
            [6, 1, 3, 2],
            [8, 4, 6, 8],
            [7, 1, 2, 6],
            [10, 5, 6, 9],
            [6, 2, 4, 7],
        ]
    )


@pytest.fixture
def complete_agreement():
    return np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]])


@pytest.fixture
def noisy_raters():
    return np.array([[1, 9, 4], [1, 8, 4], [1, 8, 5]])


@pytest.mark.parametrize(
    "icc_type, expected",
    [
        (ICCType.SingleMeasure, 0.1657),
        (ICCType.RandomK, 0.2898),
        (ICCType.FixedK, 0.7148),
    ],
)
def test_icc_disagreement(example_4x6, icc_type, expected):
    actual = icc(example_4x6, icc_type)

    assert math.isclose(
        actual, expected
    ), f"expected {actual:.4f} to be close to {expected}"


@pytest.mark.parametrize("icc_type", list(ICCType))
def test_icc_complete_agreement(complete_agreement, icc_type):
    actual = icc(complete_agreement, icc_type)

    assert actual == 1


@pytest.mark.parametrize("icc_type", list(ICCType))
def test_icc_much_noise(noisy_raters, icc_type):
    actual = icc(noisy_raters, icc_type)

    assert actual <= 0
