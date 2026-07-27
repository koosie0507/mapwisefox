import pandas as pd
import pytest


@pytest.fixture
def csv_file(tmp_path):
    """Build a CSV file from records and return its path."""

    def _csv_file(records, file_name="data.csv"):
        path = tmp_path / file_name
        pd.DataFrame(records).to_csv(path, index=False)
        return path

    return _csv_file


@pytest.fixture
def xlsx_file(tmp_path):
    """Build an Excel file from records and return its path."""

    def _xlsx_file(records, file_name="data.xlsx"):
        path = tmp_path / file_name
        pd.DataFrame(records).to_excel(path, index=False)
        return path

    return _xlsx_file
