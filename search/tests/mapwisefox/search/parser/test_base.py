import pytest

from mapwisefox.search.parser._base import DSLAdapter
from mapwisefox.search.parser._ir import (
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
)


class StubAdapter(DSLAdapter):
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


def test_adapt_output_both(adapter):
    node = OutputSpecExpr(target=OutputTarget.BOTH, child=ValueExpr(value="H"))
    res = adapter.adapt(node)
    assert res == {OutputTarget.QUERY: "VAL(H)", OutputTarget.FILTER: "VAL(H)"}


def test_adapt_unregistered(adapter):
    with pytest.raises(TypeError):
        adapter.adapt("unsupported")
