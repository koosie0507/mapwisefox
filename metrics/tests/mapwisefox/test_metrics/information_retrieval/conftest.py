import pandas as pd
import pytest


@pytest.fixture
def judgment_df():
    return pd.DataFrame(
        [
            {"id": 1, "doi": "10.1000/one", "title": "First paper", "year": 2024},
            {"id": 2, "doi": "", "title": "Second: Paper", "year": 2023},
        ]
    )


@pytest.fixture
def search_results_df():
    return pd.DataFrame(
        [
            {"doi": "10.1000/one", "title": "Different title", "year": 2020},
            {"doi": "", "title": "Second Paper", "year": 2023},
            {"doi": "10.1000/extra", "title": "Extra paper", "year": 2024},
        ]
    )


@pytest.fixture
def csv_file(tmp_path, judgment_df):
    default_name = "judgment.csv"

    def _(file_name, records):
        df = pd.DataFrame(records) if records else judgment_df
        file_name = file_name or default_name
        file_path = tmp_path / file_name
        df.to_csv(file_path, index=False)
        return file_path

    return _
