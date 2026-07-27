import pandas as pd
import pytest

from mapwisefox.metrics._utils import is_valid_path, load_df


def test_is_valid_path_accepts_csv_and_xlsx(tmp_path):
    assert is_valid_path(tmp_path / "a.csv")
    assert is_valid_path(tmp_path / "a.xlsx")
    assert not is_valid_path(tmp_path / "a.bib")
    assert not is_valid_path(tmp_path / "a.txt")


def test_load_df_reads_csv(tmp_path):
    path = tmp_path / "data.csv"
    pd.DataFrame({"id": [1, 2], "score": [1.0, 2.0]}).to_csv(path, index=False)
    df = load_df(path, index_col="id")

    assert df.loc[1, "score"] == pytest.approx(1.0)


def test_load_df_reads_xlsx(tmp_path):
    path = tmp_path / "data.xlsx"
    pd.DataFrame({"id": [1, 2], "score": [1.0, 2.0]}).to_excel(path, index=False)
    df = load_df(path, index_col="id")

    assert df.loc[1, "score"] == pytest.approx(1.0)


def test_load_df_rejects_bib(tmp_path):
    path = tmp_path / "data.bib"
    path.write_text("@article{x, title={x}}\n")

    with pytest.raises(ValueError, match="unsupported file type"):
        load_df(path)


def test_load_df_wraps_loading_errors(tmp_path):
    path = tmp_path / "data.xlsx"
    path.write_bytes(b"not a valid xlsx file content")

    with pytest.raises(ValueError, match=f"error loading file {path}"):
        load_df(path)
