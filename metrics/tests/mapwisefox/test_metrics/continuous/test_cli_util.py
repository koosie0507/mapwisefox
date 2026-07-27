import pandas as pd

from mapwisefox.metrics._types import CommonArgs
from mapwisefox.metrics.continuous._cli_util import save_xls


def test_save_xls_skips_when_no_output_file():
    args = CommonArgs()
    save_xls(pd.DataFrame({"x": [1]}), args, "Sheet")
    # No error, no file written.


def test_save_xls_creates_new_file(tmp_path):
    output = tmp_path / "out.xlsx"
    args = CommonArgs(output_file=output)
    save_xls(pd.DataFrame({"x": [1, 2]}), args, "Sheet1")

    assert output.exists()
    df = pd.read_excel(output, sheet_name="Sheet1")
    assert list(df["x"]) == [1, 2]


def test_save_xls_appends_to_existing_file(tmp_path):
    output = tmp_path / "out.xlsx"
    args = CommonArgs(output_file=output)
    save_xls(pd.DataFrame({"x": [1]}), args, "Sheet1")
    save_xls(pd.DataFrame({"y": [2]}), args, "Sheet2")

    assert "Sheet1" in pd.ExcelFile(output).sheet_names
    assert "Sheet2" in pd.ExcelFile(output).sheet_names


def test_save_xls_replaces_existing_sheet(tmp_path):
    output = tmp_path / "out.xlsx"
    args = CommonArgs(output_file=output)
    save_xls(pd.DataFrame({"x": [1]}), args, "Sheet1")
    save_xls(pd.DataFrame({"x": [2, 3]}), args, "Sheet1")

    df = pd.read_excel(output, sheet_name="Sheet1")
    assert list(df["x"]) == [2, 3]
