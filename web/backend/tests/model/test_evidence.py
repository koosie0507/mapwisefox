from datetime import datetime

import numpy as np
import pytest


LIST_PARSER_TEST_DATA = [
    ("test", ["test"]),
    ("test1;test2", ["test1", "test2"]),
    ("test1; test2", ["test1", "test2"]),
    (None, []),
    ("", []),
]
BOOL_PARSER_TEST_DATA = [
    (True, True),
    (False, False),
    ("yes", True),
    ("no", False),
    ("True", True),
    ("False", False),
    ("true", True),
    ("false", False),
    ("include", True),
    ("exclude", False),
    ("Include", True),
    ("Exclude", False),
    ("1", True),
    ("0", False),
    ("y", True),
    ("n", False),
    ("t", True),
    ("f", False),
    (None, False),
    ("", False),
]


@pytest.mark.parametrize("publication_date", ["ajdbc", "-2025", 13e-5])
def test_init_invalid_date(new_evidence, publication_date):
    with pytest.raises(ValueError) as err_proxy:
        new_evidence(1, publication_date=publication_date)

    assert (
        str(err_proxy.value)
        == f"""1 validation error for Evidence
  Value error, Invalid publication date: '{publication_date}' [type=value_error, input_value={{'cluster_id': 1, 'includ...ferencing_evidence': []}}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.11/v/value_error"""
    )


@pytest.mark.parametrize(
    "publication_date,expected",
    [
        ("2025", datetime(2025, 1, 1)),
        ("2025-06", datetime(2025, 6, 1)),
        ("2025-06-15", datetime(2025, 6, 15)),
        (None, None),
        ("", None),
        ("\r", None),
        ("\n", None),
        ("\t", None),
        (" ", None),
        ("nan", None),
        (np.nan, None),
    ],
)
def test_init_valid_publication_date(new_evidence, publication_date, expected):
    assert (
        new_evidence(1, publication_date=publication_date).publication_date == expected
    )


@pytest.mark.parametrize("author_str,expected", LIST_PARSER_TEST_DATA)
def test_init_parses_authors(new_evidence, author_str, expected):
    assert new_evidence(1, authors=author_str).authors == expected


@pytest.mark.parametrize("keyword_str,expected", LIST_PARSER_TEST_DATA)
def test_init_parses_keywords(new_evidence, keyword_str, expected):
    assert new_evidence(1, keywords=keyword_str).keywords == expected


@pytest.mark.parametrize("referencing_evidence_str,expected", LIST_PARSER_TEST_DATA)
def test_init_parses_referencing_evidence(
    new_evidence, referencing_evidence_str, expected
):
    assert (
        new_evidence(
            1, referencing_evidence=referencing_evidence_str
        ).referencing_evidence
        == expected
    )


@pytest.mark.parametrize("exclude_reason_str,expected", LIST_PARSER_TEST_DATA)
def test_init_parses_exclude_reasons(new_evidence, exclude_reason_str, expected):
    assert (
        new_evidence(1, exclude_reasons=exclude_reason_str).exclude_reasons == expected
    )


@pytest.mark.parametrize("include,expected", BOOL_PARSER_TEST_DATA)
def test_init_parses_includes(new_evidence, include, expected):
    assert new_evidence(1, include=include).include == expected


@pytest.mark.parametrize("has_pdf,expected", BOOL_PARSER_TEST_DATA)
def test_init_parses_has_pdf(new_evidence, has_pdf, expected):
    assert new_evidence(1, has_pdf=has_pdf).has_pdf == expected
