import pytest

from mapwisefox.search.parser.adapters import SpringerDSLAdapter


@pytest.fixture
def adapter():
    return SpringerDSLAdapter()


@pytest.fixture
def parsed_text(parse, adapter, request):
    text = getattr(request, "param", "")
    ir = parse(text)
    out = adapter.adapt(ir)
    return out


@pytest.mark.parametrize(
    "parsed_text,expected",
    [
        ('"machine learning" in title', 'title:"machine learning"'),
        (
            '"machine learning" in title, abstract',
            'title:"machine learning" OR Abstract:"machine learning"',
        ),
        (
            '"machine learning" in title & "machine learning" in abstract',
            '(title:"machine learning" AND Abstract:"machine learning")',
        ),
    ],
    indirect=["parsed_text"],
)
def test_springer_sanity_check(parsed_text, expected):
    assert parsed_text == expected


def test_ersa_query(parse, adapter, ersa_query_text):
    ir = parse(ersa_query_text)
    out = adapter.adapt(ir)

    assert isinstance(out, str)
