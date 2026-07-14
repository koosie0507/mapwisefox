from os import access, R_OK
from pathlib import Path

import pytest

from mapwisefox.search.dsl.parser import Parser
from mapwisefox.search.query.builder import (
    QueryBuilder,
    TitleAbsExpr,
    EvidenceTypes,
    SubjectAreas,
)


@pytest.fixture(scope="session")
def datadir():
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def parse():
    return Parser()


@pytest.fixture(scope="session")
def load_data_file(datadir):
    def _(filename):
        fpath = datadir / filename
        if not fpath.exists() or not fpath.is_file() or not access(fpath, R_OK):
            raise ValueError("the test_cases fixture requires path to a readable file")
        return fpath.read_text(encoding="utf-8")

    return _


@pytest.fixture
def test_cases(request, load_data_file, datadir):
    if not hasattr(request, "param"):
        raise ValueError("the test_cases fixture must be parametrized")
    return list(map(lambda x: x.strip(), load_data_file(request.param).split("---")))


@pytest.fixture
def ersa_query_text():
    return r"""(
  (
    ("entity resolution" | "entity alignment" | "record linkage" | "data deduplication" | "merge/purge" | "entity linking" | "entity matching")
      &
    ("system" | "tool*" | "framework" | "architect*" | "library")
  ) in title,abstract
) & (
  ("entity resolution" | "entity alignment" | "record linkage" | "data deduplication" | "merge/purge" | "entity linking" | "entity matching") in keywords
) & (
  [->filter: "english" in language & ("article" | "conference") in evidence_type & "computer science" in subject & published between "2010" and "2025"]
)"""


@pytest.fixture
def ersa_query_builder():
    er_terms = [
        "entity resolution",
        "entity alignment",
        "record linkage",
        "data deduplication",
        "merge/purge",
        "entity linking",
        "entity matching",
    ]
    qualifiers = ["system", "tool*", "framework", "architect*", "library"]
    query = QueryBuilder().year_range(2010, 2025)
    query.groups(
        query.and_group(
            query.or_group(*map(TitleAbsExpr, er_terms)),
            query.or_group(*map(TitleAbsExpr, qualifiers)),
        )
    ).doc_types(
        EvidenceTypes.ARTICLE,
        EvidenceTypes.CONFERENCE,
    ).subject_areas(
        SubjectAreas.COMPUTER_SCIENCE
    ).languages(
        "english"
    ).keywords(
        *er_terms
    )
    return query
