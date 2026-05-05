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


def test_entity_resolution_mapping_study_query(parse, adapter):
    text = r"""(
      (
        ("entity resolution" | "entity alignment" | "record linkage" | "data deduplication" | "merge/purge" | "entity linking" | "entity matching")
          &
        ("system" | "tool*" | "framework" | "architect*" | "library")
      ) in title,abstract
    ) & (
      ("system" | "tool*" | "framework" | "architect*" | "library") in keywords
    ) & (
      [->filter: "english" in language]
    ) & (
      [->filter: ("article" | "conference" | "book") in evidence_type]
    ) & (
      [->filter: "computer science" in subject]
    )"""
    ir = parse(text)
    out = adapter.adapt(ir)

    assert isinstance(out, str)
