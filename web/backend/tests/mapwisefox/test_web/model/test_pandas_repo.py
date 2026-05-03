from datetime import datetime
from unittest.mock import MagicMock, call, ANY

import pandas as pd
import pytest

from mapwisefox.web.model import PandasRepo

ALL_SHEETS = [
    "Sheet1",
    "FinalSelection",
    "ExtraColumns",
    "WithReferences",
    "WithoutClusterId1",
    "WithoutClusterId2",
]


@pytest.fixture
def excel_path(datadir, request):
    if hasattr(request, "param"):
        return datadir / request.param
    return datadir / "pandas_repo_valid_input.xlsx"


@pytest.fixture
def sheet_name(request):
    return request.param if hasattr(request, "param") else "Sheet1"


@pytest.fixture
def to_excel_mock():
    return MagicMock(spec=pd.DataFrame.to_excel)


@pytest.fixture
def excel_df(excel_path, sheet_name):
    return pd.read_excel(excel_path, sheet_name)


@pytest.fixture
def pandas_repo(excel_path, sheet_name, monkeypatch, to_excel_mock) -> PandasRepo:
    repo = PandasRepo(
        excel_path,
        sheet_name,
        aliases={
            "exclude_reason": "exclude_reasons",
            "source": "publication_venue",
            "year": "publication_date",
        },
    )
    monkeypatch.setattr(repo.dataframe, "to_excel", to_excel_mock)
    return repo


@pytest.mark.parametrize("sheet_name", ALL_SHEETS, indirect=["sheet_name"])
def test_init_pandas_repo(pandas_repo, sheet_name):
    assert pandas_repo is not None
    assert pandas_repo.dataframe is not None


@pytest.mark.parametrize("sheet_name", ALL_SHEETS, indirect=["sheet_name"])
def test_init_pandas_repo_infers_cluster_id_automatically(pandas_repo, sheet_name):
    assert pandas_repo.dataframe is not None
    assert "cluster_id" in pandas_repo.dataframe.index.names


def test_get_existing_id(pandas_repo):
    evidence = pandas_repo.get(0)

    assert evidence.cluster_id == 0
    assert evidence.authors == [
        "Zhou, Yinle",
        "Nelson, Eric",
        "Kobayashi, Fumiko",
        "Talburt, John R.",
    ]
    assert evidence.keywords == [
        "record linkage",
        "design",
        "entity resolution",
        "graduate-level er course",
        "information quality",
        "measurement",
        "corporate house-holding",
        "data quality",
    ]
    assert evidence.exclude_reasons == ["secondary study, not system, not software"]
    assert evidence.doi == "10.1145/2435221.2435226"
    assert not evidence.has_pdf
    assert evidence.referencing_evidence == []
    assert evidence.exclude_reasons == ["secondary study, not system, not software"]
    assert not evidence.include
    assert evidence.publication_venue == "ACM JOURNAL OF DATA AND INFORMATION QUALITY"
    assert (
        evidence.title
        == "A Graduate-Level Course on Entity Resolution and Information Quality: A Step toward ER Education"
    )
    assert evidence.url == "http://dx.doi.org/10.1145/2435221.2435226"
    assert evidence.pdf_url is None
    assert evidence.publication_date == datetime(2013, 1, 1)


def test_get_non_existing_id(pandas_repo):
    with pytest.raises(KeyError) as err_proxy:
        pandas_repo.get(-1)

    assert str(err_proxy.value) == "-1"


def test_update_persists_data(pandas_repo):
    evidence = pandas_repo.get(0)
    evidence.doi = "10.1145/2435221.2435227"

    pandas_repo.update(evidence)

    assert pandas_repo.dataframe.loc[0, ["doi"]].values[0] == "10.1145/2435221.2435227"


def test_update_calls_to_excel(pandas_repo, sheet_name, to_excel_mock):
    evidence = pandas_repo.get(0)
    evidence.doi = "10.1145/2435221.2435227"

    pandas_repo.update(evidence)

    assert to_excel_mock.call_count == 1
    assert to_excel_mock.call_args_list == [
        call(ANY, sheet_name, index=True, index_label="cluster_id", na_rep="")
    ]


def test_update_non_existent_cluster_id(pandas_repo, to_excel_mock):
    evidence = pandas_repo.get(0)
    evidence.cluster_id = -1

    with pytest.raises(KeyError) as err_proxy:
        pandas_repo.update(evidence)

    assert to_excel_mock.call_count == 0
    assert str(err_proxy.value) == "-1"


@pytest.mark.parametrize("current_id", [-1, 0, 1])
def test_navigate_to_first_always_returns_min_id(pandas_repo, excel_df, current_id):
    expected_id = int(excel_df.index.min())
    first_id = pandas_repo.navigate(current_id, "first")

    assert first_id == expected_id


@pytest.mark.parametrize("current_id", [-1, 0, 1])
def test_navigate_to_last_always_returns_max_id(pandas_repo, excel_df, current_id):
    expected_id = int(excel_df.index.max())
    last_id = pandas_repo.navigate(current_id, "last")

    assert last_id == expected_id


@pytest.mark.parametrize(
    "sheet_name,action",
    [
        ("Empty", "first"),
        ("Empty", "prev"),
        ("Empty", "next"),
        ("Empty", "last"),
        ("Empty", "unfilled"),
    ],
    indirect=["sheet_name"],
)
def test_navigate_to_last_empty_sheet_returns_negative(pandas_repo, action):
    actual_id = pandas_repo.navigate(15, action)

    assert actual_id == -1


def test_navigate_prev_returns_negative_for_first_item(pandas_repo):
    prev_id = pandas_repo.navigate(pandas_repo.navigate(0, "first"), "prev")

    assert prev_id == -1


def test_navigate_prev_returns_previous_id(pandas_repo, excel_df):
    expected = excel_df.index[-2]
    prev_id = pandas_repo.navigate(pandas_repo.navigate(0, "last"), "prev")

    assert prev_id == expected


def test_navigate_next_returns_next_id(pandas_repo, excel_df):
    expected = excel_df.index[1]
    next_id = pandas_repo.navigate(pandas_repo.navigate(0, "first"), "next")

    assert next_id == expected


def test_navigate_next_prev_returns_starting_id(pandas_repo):
    expected_id = 15
    actual_id = pandas_repo.navigate(pandas_repo.navigate(expected_id, "prev"), "next")

    assert actual_id == expected_id


def test_navigate_prev_next_returns_starting_id(pandas_repo):
    expected_id = 15
    actual_id = pandas_repo.navigate(pandas_repo.navigate(expected_id, "next"), "prev")

    assert actual_id == expected_id


def test_navigate_prev_oob_last_returns_last(pandas_repo):
    last_id = pandas_repo.navigate(0, "last")
    prev_id = pandas_repo.navigate(last_id + 1, "prev")

    assert prev_id == last_id


def test_navigate_next_oob_first_returns_first(pandas_repo):
    first_id = pandas_repo.navigate(0, "first")
    next_id = pandas_repo.navigate(first_id - 1, "next")

    assert next_id == first_id
