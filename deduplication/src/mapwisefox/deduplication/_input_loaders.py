from pathlib import Path

import pandas as pd

from mapwisefox.shared import input as shared_input
from mapwisefox.shared.input import DEFAULT_HEADER_ALIASES, resolve_headers


RECORD_COLUMNS = [
    "title",
    "abstract",
    "authors",
    "keywords",
    "source",
    "year",
    "doi",
    "url",
    "filename",
]


def _fill_record_defaults(frame, filename):
    frame["year"] = frame["year"].astype(int)
    frame["doi"] = frame["doi"].fillna("N/A")
    frame["url"] = frame["url"].fillna("N/A")
    frame["filename"] = filename
    return frame[RECORD_COLUMNS]


def load_csv(csv_path, mappings=None, use_tabs=False):
    frame = shared_input.load_csv(
        csv_path,
        mappings,
        separator="\t" if use_tabs else ",",
    )
    return _fill_record_defaults(frame, csv_path.stem)


def load_bib(bib_path):
    frame = shared_input.load_bib(bib_path)
    frame["filename"] = bib_path.stem
    return frame


def _load_input_files(input_dir, aliases=None):
    input_dir = Path(input_dir)
    aliases = DEFAULT_HEADER_ALIASES if aliases is None else aliases
    full_df = pd.DataFrame()
    for csv_path in input_dir.glob("*.csv"):
        frame = shared_input.load_csv(csv_path)
        frame = frame.rename(columns=resolve_headers(frame.columns, aliases))
        full_df = pd.concat([full_df, _fill_record_defaults(frame, csv_path.stem)])
    for bib_path in input_dir.glob("*.bib"):
        full_df = pd.concat([full_df, load_bib(bib_path)])
    return full_df
