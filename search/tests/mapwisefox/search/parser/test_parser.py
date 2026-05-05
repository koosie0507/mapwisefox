"""AST sanity checks.

Run with: pytest -q tests/test_ast.py
"""

from __future__ import annotations

from dataclasses import fields as dc_fields, is_dataclass

import pytest
from lark.exceptions import UnexpectedInput

from mapwisefox.search.parser import _ir


def body(query):
    assert isinstance(query, _ir.Query)
    return query.body


def assert_value(node, value, fields=()):
    assert isinstance(
        node, _ir.ValueExpr
    ), f"expected ValueExpr, got {type(node).__name__}"
    assert node.value == value
    assert tuple(node.fields) == tuple(fields)


def walk(node):
    """Yield `node` and all dataclass descendants."""
    yield node
    if is_dataclass(node):
        for f in dc_fields(node):
            v = getattr(node, f.name)
            if isinstance(v, list):
                for it in v:
                    if is_dataclass(it):
                        yield from walk(it)
            elif is_dataclass(v):
                yield from walk(v)


def test_quotes_stripped(parse):
    ast = parse('"machine learning" in title')

    assert_value(body(ast), "machine learning", ("title",))


def test_no_fields_when_attr_absent(parse):
    assert_value(body(parse('"AI"')), "AI", ())


def test_multi_field(parse):
    assert_value(
        body(parse('"deep learning" in title, abstract, keywords')),
        "deep learning",
        ("title", "abstract", "keywords"),
    )


def test_simple_and(parse):
    n = body(parse('"a" in title & "b" in abstract'))
    assert isinstance(n, _ir.BinaryExpr)
    assert n.op is _ir.BoolOp.AND
    assert_value(n.left, "a", ("title",))
    assert_value(n.right, "b", ("abstract",))


def test_simple_or(parse):
    n = body(parse('"a" in title | "b" in title'))
    assert isinstance(n, _ir.BinaryExpr)
    assert n.op is _ir.BoolOp.OR


def test_not(parse):
    n = body(parse('!"a" in title'))
    assert isinstance(n, _ir.UnaryExpr)
    assert n.op is _ir.BoolOp.NOT
    assert_value(n.child, "a", ("title",))


# ── 3. Grouping and precedence ──────────────────────────────────────────────


def test_group_preserved(parse):
    n = body(parse('("a" in title)'))
    assert isinstance(n, _ir.GroupExpr)
    assert_value(n.child, "a", ("title",))


def test_group_carries_fields(parse):
    n = body(parse('("a" | "b") in title'))
    assert isinstance(n, _ir.GroupExpr)
    assert n.fields == ["title"]
    assert isinstance(n.child, _ir.BinaryExpr)


def test_nested(parse):
    n = body(parse('("a" in title & "b" in abstract) | "c" in title'))
    assert isinstance(n, _ir.BinaryExpr)
    assert n.op is _ir.BoolOp.OR
    assert isinstance(n.left, _ir.GroupExpr)
    assert isinstance(n.left.child, _ir.BinaryExpr)


# ── 4. Match operators ──────────────────────────────────────────────────────


def test_approx(parse):
    n = body(parse('approx("data science") in title'))
    assert isinstance(n, _ir.MatchExpr)
    assert n.op.kind == "approx"
    assert n.op.arg is None
    assert n.fields == ["title"]
    assert_value(n.child, "data science")


def test_nearest(parse):
    n = body(parse('nearest (5) ("a" in abstract)'))
    assert n.op.kind == "nearest"
    assert n.op.arg == 5


@pytest.mark.parametrize("match_type", list(_ir.MatchType))
def test_match_typed(parse, match_type):
    n = body(parse(f'match({match_type.value}) ("hello world" in title)'))
    assert n.op.kind == "match"
    assert n.op.arg is match_type


# ── 5. Output spec ──────────────────────────────────────────────────────────


def test_output_query_target(parse):
    n = body(parse('[->query: "AI" in title]'))
    assert isinstance(n, _ir.OutputSpecExpr)
    assert n.target is _ir.OutputTarget.QUERY
    assert_value(n.child, "AI", ("title",))


@pytest.mark.parametrize(
    "target,enum",
    [
        ("query", _ir.OutputTarget.QUERY),
        ("filter", _ir.OutputTarget.FILTER),
        ("both", _ir.OutputTarget.BOTH),
    ],
)
def test_all_output_targets(parse, target, enum):
    n = body(parse(f'[->{target}: "x"]'))
    assert n.target is enum


# ── 6. Structural invariants ────────────────────────────────────────────────


def test_no_attr_clause_in_final_ast(parse):
    """AttrClause must be fully consumed by the transformer."""
    q = parse('("a" | "b") in title & approx("c") in abstract')
    for n in walk(q):
        assert not isinstance(n, _ir.AttrClause), f"AttrClause leaked into AST at {n}"


def test_all_expr_nodes_have_fields_attr(parse):
    """Every expression-bearing node exposes a `fields` list."""
    q = parse('("a" in title & "b") | !"c" in abstract')
    expr_types = (
        _ir.ValueExpr,
        _ir.BinaryExpr,
        _ir.GroupExpr,
        _ir.UnaryExpr,
        _ir.MatchExpr,
    )
    for n in walk(q):
        if isinstance(n, expr_types):
            assert hasattr(n, "fields") and isinstance(n.fields, list)


# ── 8. Error surface ────────────────────────────────────────────────────────


def test_unterminated_string(parse):
    with pytest.raises(UnexpectedInput):
        parse('"unterminated in title')


def test_unknown_match_op(parse):
    with pytest.raises(UnexpectedInput):
        parse('frobnicate("x") in title')
