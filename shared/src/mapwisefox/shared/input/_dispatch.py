from pathlib import Path

from mapwisefox.shared.input._bib import load_bib
from mapwisefox.shared.input._csv import load_csv
from mapwisefox.shared.input._xlsx import load_xlsx


LOADERS = {
    ".csv": load_csv,
    ".bib": load_bib,
    ".xlsx": load_xlsx,
}


def load_dataframe(path, **kwargs):
    """Load a ``.csv``, ``.bib`` or ``.xlsx`` file into a dataframe."""
    suffix = Path(path).suffix.lower()
    loader = LOADERS.get(suffix)
    if not loader:
        raise ValueError("unsupported file type", Path(path).suffix)
    return loader(path, **kwargs)
