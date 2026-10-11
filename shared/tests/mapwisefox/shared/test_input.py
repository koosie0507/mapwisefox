import pandas as pd
import pytest
from mapwisefox.shared.input import (
    DEFAULT_HEADER_ALIASES,
    load_bib,
    load_csv,
    load_dataframe,
    load_xlsx,
    resolve_headers,
)


@pytest.fixture
def wos_csv_content():
    return (
        "Author Full Names,Article Title,Source Title,Abstract,"
        "Author Keywords,Publication Year,DOI,DOI Link\n"
        "John Doe,Test Title,Test Source,Test Abstract,Key1;Key2,"
        "2023,10.1000/1,http://doi.org/1"
    )


@pytest.fixture
def bibtex_content():
    return (
        "@article{test1,\n"
        "  title = {Test Title},\n"
        "  author = {John Doe and Jane Doe},\n"
        "  journal = {Test Source},\n"
        "  year = {2023},\n"
        "  doi = {10.1000/1},\n"
        "  abstract = {Test Abstract},\n"
        "  keywords = {Key1, Key2},\n"
        "}"
    )


@pytest.fixture
def xlsx_frame():
    return pd.DataFrame(
        [
            {
                "title": "T1",
                "abstract": "A1",
                "authors": "Ada",
                "keywords": "K1",
                "source": "S1",
                "year": 2025,
                "doi": "10.1/x",
                "url": "http://x",
            }
        ]
    )


def test_load_csv_reads_dataframe(tmp_path, wos_csv_content):
    csv_file = tmp_path / "wos.csv"
    csv_file.write_text(wos_csv_content)

    frame = load_csv(csv_file)

    assert frame.iloc[0]["Author Full Names"] == "John Doe"


def test_load_csv_renames_with_mappings(tmp_path, wos_csv_content):
    csv_file = tmp_path / "wos.csv"
    csv_file.write_text(wos_csv_content)

    frame = load_csv(
        csv_file,
        {
            "Author Full Names": "authors",
            "Article Title": "title",
        },
    )

    assert frame.iloc[0]["title"] == "Test Title"
    assert frame.iloc[0]["authors"] == "John Doe"


def test_load_csv_tolerates_byte_order_mark(tmp_path, wos_csv_content):
    csv_file = tmp_path / "wos.csv"
    csv_file.write_bytes(b"\xef\xbb\xbf" + wos_csv_content.encode("utf-8"))

    frame = load_csv(csv_file)

    assert frame.columns[0] == "Author Full Names"


def test_load_csv_separates_on_tabs(tmp_path, wos_csv_content):
    csv_file = tmp_path / "wos.txt.csv"
    csv_file.write_text(wos_csv_content.replace(",", "\t"))

    frame = load_csv(csv_file, separator="\t")

    assert frame.iloc[0]["Article Title"] == "Test Title"


def test_load_csv_raw_grid_keeps_all_cells_as_strings(tmp_path):
    csv_file = tmp_path / "raw.csv"
    csv_file.write_text("title,year\nT1,2025\n,\n")

    grid = load_csv(csv_file, header=False)

    assert grid.iat[0, 0] == "title"
    assert grid.iat[0, 1] == "year"
    assert grid.iat[1, 0] == "T1"
    assert grid.iat[1, 1] == "2025"
    assert grid.iat[2, 0] == ""
    assert grid.iat[2, 1] == ""
    assert grid.iat[0, 0] == "title"


def test_load_csv_raw_grid_preserves_blank_lines(tmp_path):
    csv_file = tmp_path / "raw.csv"
    csv_file.write_text("title,year\nT1,2025\n\nT2,2024\n")

    grid = load_csv(csv_file, header=False)

    assert grid.iat[2, 0] == ""
    assert len(grid) == 4


def test_load_bib_standard_fields(tmp_path, bibtex_content):
    bib_file = tmp_path / "test.bib"
    bib_file.write_text(bibtex_content)

    frame = load_bib(bib_file)

    assert frame.iloc[0]["title"] == "Test Title"
    assert frame.iloc[0]["authors"] == "John Doe; Jane Doe"


def test_load_bib_handles_missing_entries(tmp_path):
    bib_file = tmp_path / "test.bib"
    bib_file.write_text(
        "@article{test1,\n  title = {T},\n  author = {A},\n  year = {2021},\n}"
    )

    frame = load_bib(bib_file)

    assert frame.iloc[0]["abstract"] == ""
    assert frame.iloc[0]["doi"] == "N/A"


def test_load_bib_accepts_index_col(tmp_path, bibtex_content):
    bib_file = tmp_path / "test.bib"
    bib_file.write_text(bibtex_content)

    frame = load_bib(bib_file, index_col=pd.Index(["zero"]))

    assert list(frame.index) == ["zero"]


def test_load_xlsx_reads_excel(tmp_path, xlsx_frame):
    xlsx_file = tmp_path / "sheet.xlsx"
    xlsx_frame.to_excel(xlsx_file, index=False)

    frame = load_xlsx(xlsx_file)

    assert frame.iloc[0]["title"] == "T1"


def test_load_xlsx_picks_named_sheet(tmp_path, xlsx_frame):
    workbook_file = tmp_path / "multi.xlsx"
    with pd.ExcelWriter(workbook_file) as writer:
        xlsx_frame.to_excel(writer, sheet_name="studies", index=False)
        xlsx_frame.to_excel(writer, sheet_name="other", index=False)

    frame = load_xlsx(workbook_file, sheet_name="other")

    assert len(frame) == 1


def test_load_dataframe_dispatches_by_suffix(
    tmp_path, wos_csv_content, bibtex_content, xlsx_frame
):
    csv_file = tmp_path / "wos.csv"
    csv_file.write_text(wos_csv_content)
    bib_file = tmp_path / "refs.bib"
    bib_file.write_text(bibtex_content)
    xlsx_file = tmp_path / "sheet.xlsx"
    xlsx_frame.to_excel(xlsx_file, index=False)

    assert load_dataframe(csv_file).iloc[0]["Author Full Names"] == "John Doe"
    assert load_dataframe(bib_file).iloc[0]["title"] == "Test Title"
    assert load_dataframe(xlsx_file).iloc[0]["title"] == "T1"


def test_load_dataframe_raises_for_unknown_suffix(tmp_path):
    unknown = tmp_path / "mystery.txt"
    unknown.write_text("irrelevant")

    with pytest.raises(ValueError, match="unsupported file type"):
        load_dataframe(unknown)


def test_resolve_headers_normalizes_provider_columns():
    resolved = resolve_headers(
        ["Author Full Names", "Article Title", "Unrelated"], DEFAULT_HEADER_ALIASES
    )

    assert resolved == {"Author Full Names": "authors", "Article Title": "title"}


def test_resolve_headers_keeps_first_column_per_canonical():
    resolved = resolve_headers(
        ["Source title", "Abbreviated Source Title", "source"], DEFAULT_HEADER_ALIASES
    )

    assert resolved == {"Source title": "source"}


def test_resolve_headers_ignores_unmapped_headers_without_registry():
    assert resolve_headers(["Weird Column"], {"weird column": "title"}) == {
        "Weird Column": "title"
    }
