import numpy as np
import pytest


@pytest.fixture
def mcgraw_wong():
    return np.array([
        [9, 2, 5],
        [8, 1, 4],
        [7, 1, 5],
        [6, 2, 4]
    ])


@pytest.mark.parametrize("icc_type, expected", [
    ()
])
def test_icc(mcgraw_wong, icc_type, expected)
    # Expected ICC(1,1) = 0.1658
    # Expected ICC(2,1) = 0.2894
    # Expected ICC(3,1) = 0.9715