from pathlib import Path

import bibtexparser
import pandas as pd
from bibtexparser.bparser import BibTexParser


WOS_MAPPINGS = {
    "Author Full Names": "authors",
    "Article Title": "title",
    "Source Title": "source",
    "Abstract": "abstract",
    "Author Keywords": "keywords",
    "Publication Year": "year",
    "DOI": "doi",
    "DOI Link": "url",
}
XPLORE_MAPPINGS = {
    "Document Title": "title",
    "Abstract": "abstract",
    "Author Keywords": "keywords",
    "Authors": "authors",
    "Publication Title": "source",
    "Publication Year": "year",
    "DOI": "doi",
    "PDF Link": "url",
}


FILENAME_MAPPINGS = {
    "xplore": XPLORE_MAPPINGS,
    "wos": WOS_MAPPINGS,
}


def load_csv(csv_path, mappings=None, use_tabs=False):
    df = pd.read_csv(csv_path, sep="\t" if use_tabs else ",", encoding="utf-8")
    if mappings:
        df.rename(columns=mappings, inplace=True)
    df["year"] = df["year"].astype(int)
    df["doi"] = df["doi"].fillna("N/A")
    df["url"] = df["url"].fillna("N/A")
    return df[
        ["title", "abstract", "authors", "keywords", "source", "year", "doi", "url"]
    ]


def load_bib(bib_path):
    with open(bib_path) as bibtex_file:
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
        return pd.DataFrame(records)


def _load_input_files(input_dir):
    input_dir = Path(input_dir)
    full_df = pd.DataFrame()
    for csv_path in input_dir.glob("*.csv"):
        current_df = load_csv(
            csv_path,
            FILENAME_MAPPINGS.get(csv_path.stem),
        )
        full_df = pd.concat([full_df, current_df])
    for csv_path in input_dir.glob("*.bib"):
        full_df = pd.concat([full_df, load_bib(csv_path)])
    return full_df
