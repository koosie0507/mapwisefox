import pandas as pd
import pytest

from mapwisefox.assistant.tools.dataframe import load_df


def test_load_df_reads_csv(tmp_path):
    path = tmp_path / "papers.csv"
    pd.DataFrame([{"title": "T1"}]).to_csv(path, index=False)

    result = load_df(path)

    assert result.loc[0, "title"] == "T1"


def test_load_df_reads_xlsx(tmp_path):
    path = tmp_path / "papers.xlsx"
    pd.DataFrame([{"title": "T1"}]).to_excel(path, index=False)

    result = load_df(path)

    assert result.loc[0, "title"] == "T1"


def test_load_df_reads_bibliography(tmp_path):
    path = tmp_path / "papers.bib"
    path.write_text(
        "@article{key, title={A Study}, author={Doe, Jane and Smith, John}, "
        "year={2024}, journal={Journal}, doi={10.1000/test}}"
    )

    result = load_df(path)

    assert result.loc[0, "title"] == "A Study"
    assert result.loc[0, "url"] == "https://doi.org/10.1000/test"


def test_load_df_rejects_unsupported_suffix(tmp_path):
    path = tmp_path / "papers.txt"
    path.write_text("not a table")

    with pytest.raises(ValueError, match="unsupported file type"):
        load_df(path)
