import pytest

from mapwisefox.search.parser._parser import Parser


@pytest.fixture
def sut():
    return Parser()


@pytest.mark.parametrize(
    "test_cases", ["valid_expressions.txt"], indirect=["test_cases"]
)
def test_sanity(sut, test_cases):
    for tc in test_cases:
        ast = sut(tc)

        assert ast is not None


def test_entity_resolution_architecture_query(sut):
    ast = sut(
        r"""(
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
    )

    assert ast is not None
