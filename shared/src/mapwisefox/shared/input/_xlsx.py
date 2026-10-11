import pandas as pd


def load_xlsx(path, *, sheet_name=None, index_col=None):
    """Load an Excel workbook sheet into a dataframe."""
    if sheet_name is None:
        return pd.read_excel(path, index_col=index_col)
    return pd.read_excel(path, sheet_name=sheet_name, index_col=index_col)
