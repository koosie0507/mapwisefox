from typing import Any

import pytest

from mapwisefox.search.dsl.adapters import DSLAdapter
from mapwisefox.search.dsl.parser._ir import (
    BinaryExpr,
    BoolOp,
    GroupExpr,
    MatchExpr,
    MatchOp,
    MatchType,
    OutputSpecExpr,
    OutputTarget,
    Query,
    UnaryExpr,
    ValueExpr,
    DateExpr,
)


class StubAdapter(DSLAdapter):
    def emit_date(self, node: DateExpr) -> Any:
        return f"{node.field}({node.date_lo},{node.date_hi},{node.op})"

    def emit_value(self, node: ValueExpr) -> str:
        fields = f" in {node.fields}" if node.fields else ""
        return f"VAL({node.value}{fields})"

    def emit_binary(self, node: BinaryExpr) -> str:
        return f"BIN({self.adapt(node.left)} {node.op.value} {self.adapt(node.right)})"

    def emit_not(self, node: UnaryExpr) -> str:
        return f"NOT({self.adapt(node.child)})"


@pytest.fixture
def adapter():
    return StubAdapter()


def test_adapt_query(adapter):
    node = Query(body=ValueExpr(value="test"))
    assert adapter.adapt(node) == "VAL(test)"


def test_adapt_value(adapter):
    node = ValueExpr(value="hello", fields=["title"])
    assert adapter.adapt(node) == "VAL(hello in ['title'])"


@pytest.mark.parametrize(
    "lo,hi,op,field,expected",
    [
        ("2010", None, "after", "abc", "abc(2010,None,after)"),
        ("2010", "2011", "between", "abc", "abc(2010,2011,between)"),
        (None, "2011", "before", "abc", "abc(None,2011,before)"),
    ],
)
def test_adapt_date(adapter, lo, hi, op, field, expected):
    node = DateExpr(field=field, date_lo=lo, date_hi=hi, op=op)
    assert adapter.adapt(node) == expected


def test_adapt_binary(adapter):
    node = BinaryExpr(
        left=ValueExpr(value="A"), op=BoolOp.AND, right=ValueExpr(value="B")
    )
    assert adapter.adapt(node) == "BIN(VAL(A) AND VAL(B))"


def test_adapt_unary(adapter):
    node = UnaryExpr(op=BoolOp.NOT, child=ValueExpr(value="C"))
    assert adapter.adapt(node) == "NOT(VAL(C))"


def test_adapt_group(adapter):
    node = GroupExpr(child=ValueExpr(value="D"))
    assert adapter.adapt(node) == "(VAL(D))"


def test_adapt_match_approx(adapter):
    node = MatchExpr(op=MatchOp(kind="approx"), child=ValueExpr(value="E"))
    assert adapter.adapt(node) == "VAL(E)"


def test_adapt_match_nearest(adapter):
    node = MatchExpr(op=MatchOp(kind="nearest", arg=3), child=ValueExpr(value="F"))
    assert adapter.adapt(node) == "VAL(F)"


def test_adapt_match_match(adapter):
    node = MatchExpr(
        op=MatchOp(kind="match", arg=MatchType.STRICT), child=ValueExpr(value="G")
    )
    assert adapter.adapt(node) == "VAL(G)"


def test_adapt_output_query(adapter):
    node = OutputSpecExpr(target=OutputTarget.QUERY, child=ValueExpr(value="H"))
    res = adapter.adapt(node)
    assert res == {OutputTarget.QUERY: "VAL(H)", OutputTarget.FILTER: None}


def test_adapt_output_filter(adapter):
    node = OutputSpecExpr(target=OutputTarget.FILTER, child=ValueExpr(value="H"))
    res = adapter.adapt(node)
    assert res == {OutputTarget.QUERY: None, OutputTarget.FILTER: "VAL(H)"}


def test_adapt_unregistered(adapter):
    with pytest.raises(TypeError):
        adapter.adapt("unsupported")
