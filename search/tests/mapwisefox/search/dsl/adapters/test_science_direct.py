import pytest

from mapwisefox.search.query import QueryObject
from mapwisefox.search.dsl.adapters import ScienceDirectDSLAdapter


@pytest.fixture
def adapter():
    return ScienceDirectDSLAdapter()


@pytest.fixture
def query_object(parse, adapter, request):
    text = getattr(request, "param", "")
    ir = parse(text)
    return adapter.adapt(ir)


@pytest.mark.parametrize(
    "query_object,expected",
    [
        ('"machine learning" in title', 'TITLE("machine learning")'),
        (
            '"machine learning" in title, abstract',
            '(TITLE("machine learning") OR ABSTRACT("machine learning"))',
        ),
        (
            '"machine learning" in title,abstract & "kitten" in keywords',
            '(TITLE("machine learning") OR ABSTRACT("machine learning")) AND KEYWORDS("kitten")',
        ),
    ],
    indirect=["query_object"],
)
def test_sanity_check(query_object, expected):
    assert query_object.query == expected


def test_ersa_query(parse, adapter, ersa_query_text, ersa_query_builder):
    ir = parse(ersa_query_text)
    out = adapter.adapt(ir)

    assert isinstance(out, QueryObject)
    assert out.regex == {}
    assert out.filters is not None
    assert len(out.filters) == 0
    assert (
        out.query
        == r'((TITLE(("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching") AND ("system" OR "tool*" OR "framework" OR "architect*" OR "library")) OR ABSTRACT(("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching") AND ("system" OR "tool*" OR "framework" OR "architect*" OR "library"))) AND (KEYWORDS("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching"))) AND (CONTENT-TYPE("JL") AND (PUB-DATE AFT 20100101 AND PUB-DATE BEF 20251231))'
    )
