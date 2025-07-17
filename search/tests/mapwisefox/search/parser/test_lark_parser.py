import pytest


@pytest.mark.parametrize("test_cases", ["valid_expressions.txt"], indirect=["test_cases"])
def test_valid_expressions(test_cases):
    print(tc for tc in test_cases)
