import math

import numpy as np
import pytest

from click.testing import CliRunner

from mapwisefox.metrics._cli import metrics
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


def test_icc_not_2d_raises():
    with pytest.raises(ValueError, match="2D"):
        icc(np.array([1, 2, 3]))


@pytest.mark.parametrize("shape", [(1, 2), (2, 1)])
def test_icc_too_small_returns_nan(shape):
    assert math.isnan(icc(np.zeros(shape)))


def test_icc_denominator_zero_returns_nan():
    data = np.array([[1.0, 1.0], [1.0, 1.0]])
    assert math.isnan(icc(data, ICCType.RandomK))
    assert math.isnan(icc(data, ICCType.FixedK))


def test_icc_single_measure_denominator_zero():
    data = np.array([[1.0, 1.0], [1.0, 1.0]])
    assert math.isnan(icc(data, ICCType.SingleMeasure))


def test_icc_cli_prints_and_writes(tmp_path, trusted_files, evaluated_file, csv_file):
    output = tmp_path / "out.xlsx"
    result = CliRunner().invoke(
        metrics,
        [
            "-i",
            str(trusted_files[0]),
            "-i",
            str(trusted_files[1]),
            "-t",
            "score",
            "-o",
            str(output),
            "icc",
            str(evaluated_file),
        ],
    )
    assert result.exit_code == 0
    assert "Intra-Class Correlation" in result.output
    assert "ICC(1, 1)" in result.output
    assert output.exists()
