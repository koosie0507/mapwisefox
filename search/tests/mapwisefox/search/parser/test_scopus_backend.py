import pytest

from mapwisefox.search.parser.backends import ScopusDSLAdapter


@pytest.fixture
def adapter():
    return ScopusDSLAdapter()


@pytest.fixture
def parsed_text(parse, adapter, request):
    text = getattr(request, "param", "")
    ir = parse(text)
    out = adapter.adapt(ir)
    return out


@pytest.mark.parametrize(
    "parsed_text,expected",
    [
        ('"machine learning" in title', 'TITLE("machine learning")'),
        ('"machine learning" in title, abstract', 'TITLE-ABS("machine learning")'),
        (
            '"machine learning" in title & "machine learning" in abstract',
            'TITLE("machine learning") AND ABS("machine learning")',
        ),
    ],
    indirect=["parsed_text"],
)
def test_springer_sanity_check(parsed_text, expected):
    assert parsed_text == expected
