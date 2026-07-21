import pytest
from mapwisefox.deduplication._input_loaders import (
    load_csv,
    load_bib,
    _load_input_files,
    WOS_MAPPINGS,
    XPLORE_MAPPINGS,
)


@pytest.fixture
def sample_csv_content():
    return (
        "Author Full Names,Article Title,Source Title,Abstract,Author Keywords,Publication Year,DOI,DOI Link\n"
        "John Doe,Test Title,Test Source,Test Abstract,Key1;Key2,2023,10.1000/1,http://doi.org/1"
    )


@pytest.fixture
def sample_bib_content():
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


def test_load_csv_with_wos_mappings(tmp_path, sample_csv_content):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(sample_csv_content)

    df = load_csv(csv_file, mappings=WOS_MAPPINGS)

    assert df.iloc[0]["title"] == "Test Title"


def test_load_csv_with_xplore_mappings(tmp_path):
    csv_file = tmp_path / "test.csv"
    content = (
        "Document Title,Abstract,Author Keywords,Authors,Publication Title,Publication Year,DOI,PDF Link\n"
        "Xplore Title,X Abstract,X Key,X Author,X Source,2022,10.1000/2,http://xplore.org/2"
    )
    csv_file.write_text(content)

    df = load_csv(csv_file, mappings=XPLORE_MAPPINGS)

    assert df.iloc[0]["title"] == "Xplore Title"


def test_load_csv_fills_na_values(tmp_path):
    csv_file = tmp_path / "test.csv"
    content = (
        "title,abstract,authors,keywords,source,year,doi,url\n"
        "T1,A1,Au1,K1,S1,2021,, "
    )
    csv_file.write_text(content)

    df = load_csv(csv_file)

    assert df.iloc[0]["doi"] == "N/A"


def test_load_bib_standard_fields(tmp_path, sample_bib_content):
    bib_file = tmp_path / "test.bib"
    bib_file.write_text(sample_bib_content)

    df = load_bib(bib_file)

    assert df.iloc[0]["title"] == "Test Title"


def test_load_bib_handles_missing_abstract(tmp_path):
    bib_file = tmp_path / "test.bib"
    content = "@article{test1,\n  title = {T},\n  author = {A},\n  year = {2021},\n}"
    bib_file.write_text(content)

    df = load_bib(bib_file)

    assert df.iloc[0]["abstract"] == ""


def test_load_bib_formats_authors(tmp_path, sample_bib_content):
    bib_file = tmp_path / "test.bib"
    bib_file.write_text(sample_bib_content)

    df = load_bib(bib_file)

    assert df.iloc[0]["authors"] == "John Doe; Jane Doe"


def test_load_input_files_aggregates_csv_and_bib(
    tmp_path, sample_csv_content, sample_bib_content
):
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    (input_dir / "wos.csv").write_text(sample_csv_content)
    (input_dir / "test.bib").write_text(sample_bib_content)

    df = _load_input_files(input_dir)

    assert len(df) == 2


def test_load_input_files_handles_empty_dir(tmp_path):
    input_dir = tmp_path / "empty"
    input_dir.mkdir()

    df = _load_input_files(input_dir)

    assert df.empty
