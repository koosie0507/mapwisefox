import pytest

from mapwisefox.search.query import QueryObject
from mapwisefox.search.dsl.adapters import WebOfScienceDSLAdapter


@pytest.fixture
def adapter():
    return WebOfScienceDSLAdapter()


@pytest.fixture
def query_object(parse, adapter, request):
    text = getattr(request, "param", "")
    ir = parse(text)
    return adapter.adapt(ir)


@pytest.mark.parametrize(
    "query_object,expected",
    [
        ('"machine learning" in title', 'TI=("machine learning")'),
        (
            '"machine learning" in title, abstract',
            '(TI=("machine learning") OR AB=("machine learning"))',
        ),
        (
            '"machine learning" in title,abstract & "kitten" in keywords',
            '(TI=("machine learning") OR AB=("machine learning")) AND AK=("kitten")',
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
    assert out.regex == {}
    assert out.filters is not None
    assert len(out.filters) == 0
    assert (
        out.query
        == r'((TI=(("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching") AND ("system" OR "tool*" OR "framework" OR "architect*" OR "library")) OR AB=(("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching") AND ("system" OR "tool*" OR "framework" OR "architect*" OR "library"))) AND (AK=("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching"))) AND (LA=("English") AND DT=("Article") AND WC=("Computer Science") AND DOP=(2010-01-01/2025-12-31))'
    )
