import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock, patch
from mapwisefox.deduplication._deduper import (
    _clean_value,
    _clean_record,
    _url_relevance,
    _merge_cluster,
    _merge_clusters,
    _setup_deduper,
    _run_dedupe,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        [
            {
                "title": "Title 1",
                "authors": "A1",
                "source": "S1",
                "keywords": "K1;K2",
                "abstract": "Ab1",
                "doi": "10.1",
                "url": "url1",
                "year": 2020,
                "filename": "A",
            },
            {
                "title": "Title 2",
                "authors": "A2",
                "source": "S2",
                "keywords": "K2;K3",
                "abstract": "Ab2",
                "doi": "10.2",
                "url": "url2",
                "year": 2021,
                "filename": "B",
            },
        ]
    )


@pytest.mark.parametrize(
    "val, expected",
    [
        ("  Hello  ", "hello"),
        ("'Hello'", "hello"),
        ('"Hello"', "hello"),
        ("\nHello\t", "hello"),
        (123, "123"),
        (None, "none"),
    ],
)
def test_clean_value(val, expected):
    assert _clean_value(val) == expected


def test_clean_record():
    record = {"title": " Title ", "doi": "'10.1'"}
    assert _clean_record(record) == {"title": "title", "doi": "10.1"}


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://doi.org/10.1", 1),
        ("https://google.com", 2),
        ("N/A", 0),
        (None, 0),
    ],
)
def test_url_relevance(url, expected):
    assert _url_relevance(url) == expected


def test_merge_cluster_representative_selection():
    df = pd.DataFrame(
        [
            {
                "title": "T1",
                "authors": "A1",
                "source": "S1",
                "keywords": "K1",
                "abstract": "Ab1",
                "doi": "10.1",
                "url": "u1",
                "year": 2020,
                "confidence": 0.5,
                "filename": "A",
            },
            {
                "title": "T2",
                "authors": "A2",
                "source": "S2",
                "keywords": "K2",
                "abstract": "Ab2",
                "doi": "10.2",
                "url": "u2",
                "year": 2021,
                "confidence": 0.9,
                "filename": "B",
            },
        ]
    )
    result = _merge_cluster(df)
    assert result["title"] == "T2"


def test_merge_cluster_keyword_aggregation():
    df = pd.DataFrame(
        [
            {
                "title": "T1",
                "authors": "A1",
                "source": "S1",
                "keywords": "K1;K2",
                "abstract": "Ab1",
                "doi": "10.1",
                "url": "u1",
                "year": 2020,
                "confidence": 0.5,
                "filename": "A",
            },
            {
                "title": "T2",
                "authors": "A2",
                "source": "S2",
                "keywords": "K2;K3",
                "abstract": "Ab2",
                "doi": "10.2",
                "url": "u2",
                "year": 2021,
                "confidence": 0.9,
                "filename": "B",
            },
        ]
    )
    result = _merge_cluster(df)
    assert "k1" in result["keywords"].lower()
    assert "k2" in result["keywords"].lower()
    assert "k3" in result["keywords"].lower()


def test_merge_clusters_aggregates_multiple_groups(sample_df):
    sample_df["cluster_id"] = [0, 1]
    sample_df["confidence"] = [1.0, 1.0]

    result = _merge_clusters(sample_df)

    assert len(result) == 2


def test_merge_clusters_aggregates_sources(sample_df):
    sample_df["cluster_id"] = [1, 1]
    sample_df["confidence"] = [0.8, 1.0]
    result = _merge_clusters(sample_df)

    assert len(result) == 1
    assert result["sources"].tolist() == ["(A,0); (B,1)"]


@patch("mapwisefox.deduplication._deduper._load_pretrained")
def test_setup_deduper_uses_pretrained(mock_load, tmp_path):
    mock_dedupe = MagicMock()
    mock_load.return_value = mock_dedupe

    result = _setup_deduper({}, tmp_path / "settings", tmp_path / "training", None)

    assert result == mock_dedupe


@patch("mapwisefox.deduplication._deduper.dedupe.Dedupe")
@patch("mapwisefox.deduplication._deduper.dedupe.console_label")
@patch("mapwisefox.deduplication._deduper._load_pretrained", return_value=None)
def test_setup_deduper_trains_new(mock_load, mock_label, mock_dedupe_cls, tmp_path):
    mock_dedupe = mock_dedupe_cls.return_value

    _setup_deduper({}, tmp_path / "settings", tmp_path / "training", None)

    mock_dedupe.train.assert_called_once()


@patch("mapwisefox.deduplication._deduper._setup_deduper")
def test_run_dedupe_adds_columns(mock_setup, sample_df):
    mock_deduper = MagicMock()
    mock_setup.return_value = mock_deduper
    mock_deduper.partition.return_value = [([0, 1], [0.9, 0.8])]

    result = _run_dedupe(sample_df, Path("t"), Path("s"))

    assert "cluster_id" in result.columns
    assert "confidence" in result.columns


@patch("mapwisefox.deduplication._deduper._setup_deduper")
def test_run_dedupe_defaults_threshold_to_half(mock_setup, sample_df):
    mock_deduper = MagicMock()
    mock_setup.return_value = mock_deduper
    mock_deduper.partition.return_value = [([0, 1], [0.9, 0.8])]

    _run_dedupe(sample_df, Path("t"), Path("s"))

    assert mock_deduper.partition.call_args.args[1] == 0.5


@patch("mapwisefox.deduplication._deduper._setup_deduper")
def test_run_dedupe_passes_custom_threshold_to_partition(mock_setup, sample_df):
    mock_deduper = MagicMock()
    mock_setup.return_value = mock_deduper
    mock_deduper.partition.return_value = [([0, 1], [0.9, 0.8])]

    _run_dedupe(sample_df, Path("t"), Path("s"), threshold=0.7)

    assert mock_deduper.partition.call_args.args[1] == 0.7
