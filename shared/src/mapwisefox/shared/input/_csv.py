import pandas as pd


def load_csv(
    source,
    mappings=None,
    *,
    separator=",",
    encoding="utf-8-sig",
    header=True,
    index_col=None,
):
    """Load a CSV export into a dataframe, tolerating a UTF-8 byte order mark.

    With ``header=False`` returns an all-string grid including the header row
    itself, for consumers that need to inspect or validate raw columns first.
    """
    if not header:
        return pd.read_csv(
            source,
            sep=separator,
            encoding=encoding,
            header=None,
            dtype=str,
            keep_default_na=False,
            skip_blank_lines=False,
        )
    frame = pd.read_csv(source, sep=separator, encoding=encoding, index_col=index_col)
    if mappings:
        frame = frame.rename(columns=mappings)
    return frame
