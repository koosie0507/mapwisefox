import pytest

from mapwisefox.search.dsl.adapters import SpringerDSLAdapter
from mapwisefox.search.query import QueryObject


@pytest.fixture
def adapter():
    return SpringerDSLAdapter()


@pytest.fixture
def query_obj(parse, adapter, request):
    text = getattr(request, "param", "")
    ir = parse(text)
    out = adapter.adapt(ir)
    return out


@pytest.mark.parametrize(
    "query_obj,expected_query,expected_regex",
    [
        ('"machine learning" in title', "", {"title": r"machine\slearning"}),
        (
            '"machine learning" in title, abstract',
            "",
            {"title": r"machine\slearning", "abstract": r"machine\slearning"},
        ),
        (
            '"machine learning" in title & "machine learning" in abstract',
            "",
            {"title": r"machine\slearning", "abstract": r"machine\slearning"},
        ),
        (
            '"machine learning" in title & "machine learning" in keyword',
            'keyword:"machine learning"',
            {"title": r"machine\slearning"},
        ),
    ],
    indirect=["query_obj"],
)
def test_springer_sanity_check(query_obj, expected_query, expected_regex):
    assert query_obj.query == expected_query
    assert query_obj.regex == expected_regex


@pytest.mark.parametrize(
    "query_obj,expected_query,expected_regex",
    [
        (
            'near[5]("machine", "learning") in keyword',
            'keyword:"machine" NEAR/5 "learning"',
            {},
        ),
        (
            # title/abstract are regex-only for Springer, so `near(...)`
            # degrades to the distance-aware regex fallback, not NEAR/n.
            'near[5]("machine", "learning") in title',
            "",
            {
                "title": r"^(?=.*(?:\bmachine\b(?:\W+\w+){0,5}\W+\blearning\b"
                r"|\blearning\b(?:\W+\w+){0,5}\W+\bmachine\b))"
            },
        ),
        (
            'near[5]("machine", "learning") in title, keyword',
            'keyword:"machine" NEAR/5 "learning"',
            {
                "title": r"^(?=.*(?:\bmachine\b(?:\W+\w+){0,5}\W+\blearning\b"
                r"|\blearning\b(?:\W+\w+){0,5}\W+\bmachine\b))"
            },
        ),
    ],
    indirect=["query_obj"],
)
def test_springer_near(query_obj, expected_query, expected_regex):
    assert query_obj.query == expected_query
    assert query_obj.regex == expected_regex


def test_ersa_query(parse, adapter, ersa_query_text):
    ir = parse(ersa_query_text)
    out = adapter.adapt(ir)

    assert isinstance(out, QueryObject)
    assert out.filters is not None
    assert (
        out.query
        == '(keyword:"entity resolution" OR keyword:"entity alignment" OR keyword:"record linkage" OR keyword:"data deduplication" OR keyword:"merge/purge" OR keyword:"entity linking" OR keyword:"entity matching") AND (type:"Journal" AND datefrom:"2010-01-01" AND dateto:"2025-12-31")'
    )
    assert out.regex == {
        "title": r"^(?=.*(entity\sresolution|entity\salignment|record\slinkage|data\sdeduplication|merge/purge|entity\slinking|entity\smatching))(?=.*(system|tool\w*|framework|architect\w*|library))",
        "abstract": r"^(?=.*(entity\sresolution|entity\salignment|record\slinkage|data\sdeduplication|merge/purge|entity\slinking|entity\smatching))(?=.*(system|tool\w*|framework|architect\w*|library))",
    }
