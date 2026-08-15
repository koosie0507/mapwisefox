from functools import partial

import pandas as pd
from bibtexparser import load as load_bibtex
from bibtexparser.bparser import BibTexParser


def _read_bibliography(path, index_col=None):
    with open(path) as bibtex_file:
        parser = BibTexParser(common_strings=True)
        bib_database = load_bibtex(bibtex_file, parser=parser)
        records = [
            {
                "title": entry["title"],
                "abstract": entry.get("abstract", ""),
                "authors": entry.get("author", "").replace(" and", ";"),
                "keywords": entry.get("keywords", "").replace(", ", "; "),
                "source": entry.get("booktitle", entry.get("journal", "")),
                "year": int(entry["year"]),
                "doi": entry.get("doi", "N/A"),
                "url": entry.get(
                    "url",
                    f"https://doi.org/{entry['doi']}" if "doi" in entry else "N/A",
                ),
            }
            for entry in bib_database.entries
        ]
        return pd.DataFrame(records, index=index_col)


def load_df(path, index_col=None, sheet_name=None):
    """Load a ``.bib``, ``.csv`` or ``.xlsx`` file into a pandas DataFrame.

    Args:
        path: path to ``.bib`` or ``.csv`` or ``.xlsx`` file

    Raises:
        ValueError: if ``path`` is not a ``.csv`` or ``.xlsx`` file

    Returns:
        ``pandas.DataFrame`` containing bibliography data
    """
    fh = {
        ".bib": _read_bibliography,
        ".xlsx": (
            pd.read_excel
            if sheet_name is None
            else partial(pd.read_excel, sheet_name=sheet_name)
        ),
        ".csv": pd.read_csv,
    }
    file_loader = fh.get(path.suffix)
    if not file_loader:
        raise ValueError("unsupported file type", path.suffix)
    return file_loader(path, index_col=index_col)
