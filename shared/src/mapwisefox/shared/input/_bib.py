import bibtexparser
import pandas as pd
from bibtexparser.bparser import BibTexParser


def load_bib(path, *, index_col=None):
    """Load a BibTeX bibliography into a dataframe using MapwiseFox record fields."""
    with open(path) as bibtex_file:
        parser = BibTexParser(common_strings=True)
        bib_database = bibtexparser.load(bibtex_file, parser=parser)
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
