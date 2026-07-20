import pytest

from mapwisefox.search.query import QueryObject
from mapwisefox.search.dsl.adapters import XploreDSLAdapter


@pytest.fixture
def adapter():
    return XploreDSLAdapter()


@pytest.fixture
def query_object(parse, adapter, request):
    text = getattr(request, "param", "")
    ir = parse(text)
    return adapter.adapt(ir)


@pytest.mark.parametrize(
    "query_object,expected",
    [
        ('"machine learning" in title', '"Document Title":"machine learning"'),
        (
            '"machine learning" in title, abstract',
            '("Document Title":"machine learning" OR "Abstract":"machine learning")',
        ),
        (
            '"machine learning" in title,abstract & "kitten" in keywords',
            '("Document Title":"machine learning" OR "Abstract":"machine learning") AND "Author Keywords":"kitten"',
        ),
    ],
    indirect=["query_object"],
)
def test_sanity_check(query_object, expected):
    assert query_object.query == expected


def test_ersa_query(parse, adapter, ersa_query_text):
    ir = parse(ersa_query_text)
    out = adapter.adapt(ir)

    assert isinstance(out, QueryObject)
    assert (
        out.query
        == '((("Document Title":"entity resolution" OR "Abstract":"entity resolution") OR ("Document Title":"entity alignment" OR "Abstract":"entity alignment") OR ("Document Title":"record linkage" OR "Abstract":"record linkage") OR ("Document Title":"data deduplication" OR "Abstract":"data deduplication") OR ("Document Title":"merge/purge" OR "Abstract":"merge/purge") OR ("Document Title":"entity linking" OR "Abstract":"entity linking") OR ("Document Title":"entity matching" OR "Abstract":"entity matching")) AND (("Document Title":"system" OR "Abstract":"system") OR ("Document Title":tool* OR "Abstract":tool*) OR ("Document Title":"framework" OR "Abstract":"framework") OR ("Document Title":architect* OR "Abstract":architect*) OR ("Document Title":"library" OR "Abstract":"library"))) AND ("Author Keywords":"entity resolution" OR "Author Keywords":"entity alignment" OR "Author Keywords":"record linkage" OR "Author Keywords":"data deduplication" OR "Author Keywords":"merge/purge" OR "Author Keywords":"entity linking" OR "Author Keywords":"entity matching")'
    )
    assert out.regex == {}
    assert out.filters is not None
    assert len(out.filters) == 3
    assert "content_type" in out.filters
    assert out.filters["content_type"] == ["Journals", "Conferences"]
    assert out.filters["end_year"] == ["2025"]
    assert out.filters["start_year"] == ["2010"]
