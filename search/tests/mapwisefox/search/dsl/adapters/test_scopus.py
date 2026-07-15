import pytest

from mapwisefox.search.query import QueryObject
from mapwisefox.search.dsl.adapters import ScopusDSLAdapter


@pytest.fixture
def adapter():
    return ScopusDSLAdapter()


@pytest.fixture
def query_object(parse, adapter, request):
    text = getattr(request, "param", "")
    ir = parse(text)
    return adapter.adapt(ir)


@pytest.mark.parametrize(
    "query_object,expected",
    [
        ('"machine learning" in title', 'TITLE("machine learning")'),
        ('"machine learning" in title, abstract', 'TITLE-ABS("machine learning")'),
        (
            '"machine learning" in title & "machine learning" in abstract',
            'TITLE("machine learning") AND ABS("machine learning")',
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
        == r'((TITLE-ABS(("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching") AND ("system" OR "tool*" OR "framework" OR "architect*" OR "library"))) AND (AUTHKEY("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching"))) AND (LANGUAGE("english") AND DOCTYPE("ar" OR "cp") AND SUBJAREA("COMP") AND (PUBYEAR AFT 2009 AND PUBYEAR BEF 2026))'
    )
