from pathlib import Path

import pytest
from lark.exceptions import LarkError


@pytest.fixture(scope="module")
def valid_expressions():
    data_file = Path(__file__).parents[4] / "data" / "valid_expressions.txt"
    content = data_file.read_text(encoding="utf-8")
    expressions = [expr.strip() for expr in content.split("---")]
    return [expr for expr in expressions if expr]


def test_all_valid_expressions_parse(parse, valid_expressions):
    failed_expressions = []

    for i, expr in enumerate(valid_expressions, start=1):
        try:
            result = parse(expr)
            # Verify that we got a valid result
            assert result is not None, f"Parser returned None for expression #{i}"
        except LarkError as e:
            failed_expressions.append({
                "index": i,
                "expression": expr,
                "error": str(e)
            })
        except Exception as e:
            failed_expressions.append({
                "index": i,
                "expression": expr,
                "error": f"Unexpected error: {type(e).__name__}: {str(e)}"
            })

    if failed_expressions:
        error_lines = [
            f"\n{len(failed_expressions)} expression(s) failed to parse:\n"
        ]
        for failure in failed_expressions:
            error_lines.append(
                f"  Expression #{failure['index']}:\n"
                f"    {failure['expression']}\n"
                f"    Error: {failure['error']}\n"
            )
        pytest.fail("".join(error_lines))


@pytest.mark.parametrize("expression_idx", range(20))
def test_individual_valid_expression(parse, valid_expressions, expression_idx):
    if expression_idx >= len(valid_expressions):
        pytest.skip(f"Only {len(valid_expressions)} expressions available")

    expr = valid_expressions[expression_idx]

    try:
        result = parse(expr)
        assert result is not None, "Parser returned None"
    except LarkError as e:
        pytest.fail(
            f"Failed to parse expression #{expression_idx + 1}:\n"
            f"  Expression: {expr}\n"
            f"  Error: {str(e)}"
        )
