from pathlib import Path

from mapwisefox.shared.input import load_csv, load_xlsx


SUPPORTED_FILE_HANDLERS = {
    ".xlsx": load_xlsx,
    ".csv": load_csv,
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
    file_handler = SUPPORTED_FILE_HANDLERS.get(path.suffix)
    if not file_handler:
        raise ValueError("unsupported file type", path.suffix)
    try:
        return file_handler(path, index_col=index_col)
    except Exception as e:
        raise ValueError(f"error loading file {path}") from e
