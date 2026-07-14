import pytest

from mapwisefox.search.dsl.adapters import AcmDSLAdapter
from mapwisefox.search.query import QueryObject


@pytest.fixture
def adapter():
    return AcmDSLAdapter()


@pytest.fixture
def query_obj(parse, adapter, request):
    text = getattr(request, "param", "")
    return adapter.adapt(parse(text))


@pytest.mark.parametrize(
    "query_obj,expected_query,expected_filters",
    [
        ('"machine learning" in title', 'Title:"machine learning"', {}),
        (
            '"machine learning" in title,abstract',
            'Title:"machine learning" OR Abstract:"machine learning"',
            {},
        ),
        (
            '"machine learning" in title & "conference" in evidence_type',
            'Title:"machine learning"',
            {"Article Type": "Research Article"},
        ),
        (
            '("image processing" & "CNN") in abstract',
            'Abstract:("image processing" AND "CNN")',
            {},
        ),
    ],
    indirect=["query_obj"],
)
def test_sanity(query_obj, expected_query, expected_filters):
    assert isinstance(query_obj, QueryObject)

    assert query_obj.regex == ""
    assert query_obj.query == expected_query
    assert query_obj.filters == expected_filters


def test_ersa_query(parse, adapter, ersa_query_text):
    ir = parse(ersa_query_text)
    q = adapter.adapt(ir)

    assert isinstance(q, QueryObject)
    assert (
        q.query
        == '(Title:(("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching") AND ("system" OR "tool*" OR "framework" OR "architect*" OR "library")) OR Abstract:(("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching") AND ("system" OR "tool*" OR "framework" OR "architect*" OR "library"))) AND (Keyword:("entity resolution" OR "entity alignment" OR "record linkage" OR "data deduplication" OR "merge/purge" OR "entity linking" OR "entity matching"))'
    )
    assert q.filters is not None
    assert "E-Publication Date" in q.filters
    assert q.filters["E-Publication Date"] == "(01/01/2010 TO 12/31/2025)"
    assert "Article Type" in q.filters
    assert q.filters["Article Type"] == "Research Article"
