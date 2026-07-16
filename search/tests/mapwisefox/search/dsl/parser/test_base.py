import pytest

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
from mapwisefox.search.query import QueryObject


def test_adapt_query(stub_adapter):
    node = Query(body=ValueExpr(value="test"))
    assert stub_adapter.adapt(node) == QueryObject(query="VAL(test)")


def test_adapt_value(stub_adapter):
    node = ValueExpr(value="hello", fields=["title"])
    assert stub_adapter.adapt(node).query == "VAL(hello in ['title'])"


@pytest.mark.parametrize(
    "lo,hi,op,field,expected",
    [
        ("2010", None, "after", "abc", "abc(2010,None,after)"),
        ("2010", "2011", "between", "abc", "abc(2010,2011,between)"),
        (None, "2011", "before", "abc", "abc(None,2011,before)"),
    ],
)
def test_adapt_date(stub_adapter, lo, hi, op, field, expected):
    node = DateExpr(field=field, date_lo=lo, date_hi=hi, op=op)
    assert stub_adapter.adapt(node).query == expected


def test_adapt_binary(stub_adapter):
    node = BinaryExpr(
        left=ValueExpr(value="A"), op=BoolOp.AND, right=ValueExpr(value="B")
    )
    assert stub_adapter.adapt(node).query == "VAL(A) and VAL(B)"


def test_adapt_unary(stub_adapter):
    node = UnaryExpr(op=BoolOp.NOT, child=ValueExpr(value="C"))
    assert stub_adapter.adapt(node).query == "NOT VAL(C)"


def test_adapt_group(stub_adapter):
    node = GroupExpr(child=ValueExpr(value="D"))
    result = stub_adapter.adapt(node)

    assert isinstance(result, QueryObject)
    assert result.query == "VAL(D)"


def test_adapt_match_approx(stub_adapter):
    node = MatchExpr(op=MatchOp(kind="approx"), child=ValueExpr(value="E"))
    assert stub_adapter.adapt(node).query == "VAL(E)"


def test_adapt_match_nearest(stub_adapter):
    node = MatchExpr(op=MatchOp(kind="nearest", arg=3), child=ValueExpr(value="F"))
    assert stub_adapter.adapt(node).query == "VAL(F)"


def test_adapt_match_match(stub_adapter):
    node = MatchExpr(
        op=MatchOp(kind="match", arg=MatchType.STRICT), child=ValueExpr(value="G")
    )
    assert stub_adapter.adapt(node).query == "VAL(G)"


def test_adapt_output_query(stub_adapter):
    node = OutputSpecExpr(target=OutputTarget.QUERY, child=ValueExpr(value="H"))
    res = stub_adapter.adapt(node)
    assert res == QueryObject(query="VAL(H)")


def test_adapt_output_filter(stub_adapter):
    node = OutputSpecExpr(target=OutputTarget.FILTER, child=ValueExpr(value="H"))
    res = stub_adapter.adapt(node)
    assert res == QueryObject(query="VAL(H)")


def test_adapt_unregistered(stub_adapter):
    with pytest.raises(TypeError):
        stub_adapter.adapt("unsupported")
