from pathlib import Path

import pandas as pd


SUPPORTED_FILE_HANDLERS = {
    ".xlsx": pd.read_excel,
    ".csv": pd.read_csv,
}


def is_valid_path(fp: Path) -> bool:
    return fp.suffix in SUPPORTED_FILE_HANDLERS


def load_df(path, index_col=None):
    """Load a ``.csv`` or ``.xlsx`` file into a pandas DataFrame.

    Args:
        path: path to ``.csv`` or ``.xlsx`` file

    Raises:
        ValueError: if ``path`` is not a ``.csv`` or ``.xlsx`` file

    Returns:
        ``pandas.DataFrame`` containing file data
    """
    file_loader = SUPPORTED_FILE_HANDLERS.get(path.suffix)
    if not file_loader:
        raise ValueError("unsupported file type", path.suffix)
    try:
        return file_loader(path, index_col=index_col)
    except Exception as e:
        raise ValueError(f"error loading file {path}") from e
