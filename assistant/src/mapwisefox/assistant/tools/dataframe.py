from mapwisefox.shared.input import load_dataframe


def load_df(path, index_col=None, sheet_name=None):
    """Load a ``.bib``, ``.csv`` or ``.xlsx`` file into a pandas DataFrame.

    Args:
        path: path to ``.bib`` or ``.csv`` or ``.xlsx`` file
        index_col: optional column to use as row labels
        sheet_name: optional worksheet name for ``.xlsx`` files

    Raises:
        ValueError: if ``path`` is not a ``.csv``, ``.bib`` or ``.xlsx`` file

    Returns:
        ``pandas.DataFrame`` containing bibliography data
    """
    if sheet_name is None:
        return load_dataframe(path, index_col=index_col)
    return load_dataframe(path, sheet_name=sheet_name, index_col=index_col)
