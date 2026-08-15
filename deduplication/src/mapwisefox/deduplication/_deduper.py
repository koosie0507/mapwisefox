import os
from functools import partial
from os import R_OK, access
from pathlib import Path

import dedupe
import pandas as pd
from dedupe import variables as v


_DEFAULT_FIELDS = [
    "title",
    "authors",
    "keywords",
    "doi",
    "source",
]


def _clean_value(value):
    return str(value).lower().strip("\"' \t\n\r")


def _clean_record(record):
    return {key: _clean_value(value) for key, value in record.items()}


def _load_pretrained(settings_file: Path):
    if not (settings_file.is_file() and access(settings_file, R_OK)):
        return None

    with open(settings_file, "rb") as f:
        return dedupe.StaticDedupe(f)


def _prepare_training(deduper, dedupe_data, training_file):
    print("preparing training data")
    if training_file.is_file() and access(training_file, R_OK):
        print("reading labeled examples from ", training_file)
        with open(training_file, "r") as f:
            deduper.prepare_training(dedupe_data, f)
    else:
        deduper.prepare_training(dedupe_data)


def _load_dedupe_data(df):
    df_dict = df.to_dict(orient="records")
    dedupe_data = {idx: _clean_record(record) for idx, record in enumerate(df_dict)}
    return dedupe_data


def _setup_deduper(dedupe_data, settings_file, training_file, fields=None):
    fields = list(map(v.String, fields or _DEFAULT_FIELDS))
    if (deduper := _load_pretrained(settings_file)) is not None:
        return deduper

    deduper = dedupe.Dedupe(fields)
    _prepare_training(deduper, dedupe_data, training_file)
    print("labeling using active learning")
    dedupe.console_label(deduper)
    print("training")
    deduper.train()
    training_file.parent.mkdir(parents=True, exist_ok=True)
    with open(training_file, "w") as tf:
        deduper.write_training(tf)
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_file, "wb") as sf:
        deduper.write_settings(sf)
    return deduper


def _run_dedupe(df, training_file, settings_file, threshold=0.5, fields=None):
    dedupe_df = df.copy()
    dedupe_df.reset_index(drop=True, inplace=True)
    print("load input...")
    dedupe_data = _load_dedupe_data(dedupe_df)
    print("blocking and indexing...")
    deduper = _setup_deduper(dedupe_data, settings_file, training_file, fields)
    print("matching & clustering...")
    clustered_dupes = deduper.partition(dedupe_data, threshold)
    print("  * # duplicate sets =", len(clustered_dupes))
    clusters = {}
    for cluster_id, (records, scores) in enumerate(clustered_dupes):
        for record_id, score in zip(records, scores):
            clusters[record_id] = {
                "cluster_id": cluster_id,
                "confidence_score": score,
            }
    dedupe_df["cluster_id"] = dedupe_df.index.map(lambda i: clusters[i]["cluster_id"])
    dedupe_df["confidence"] = dedupe_df.index.map(
        lambda i: clusters[i]["confidence_score"]
    )
    return dedupe_df


def _url_relevance(url):
    if not url or url == "N/A":
        return 0
    elif "doi.org" in url:
        return 1
    return 2


def _is_usable_value(val):
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, str):
        return len(val.strip()) > 0
    return True


def _extract_single_value(item_value):
    yield item_value


def _keywords(item_value, separator):
    for x in str(item_value).split(separator):
        yield x.strip().lower()


def _get_repr_property_with_fallback(
    group,
    prop,
    use_repr=True,
    value_handler=_extract_single_value,
    separator=os.linesep,
):
    if use_repr:
        repr_val = group.loc[group["confidence"].idxmax(), prop]
        if _is_usable_value(repr_val):
            return repr_val

    seen = set()
    usable_values = []
    for value in filter(_is_usable_value, group[prop]):
        for atom in value_handler(value):
            if atom in seen:
                continue
            usable_values.append(atom)
            seen.add(atom)

    return separator.join(usable_values)


def _merge_cluster(group):
    repr_idx = group["confidence"].idxmax()
    abstract = _get_repr_property_with_fallback(group, "abstract")
    keywords = _get_repr_property_with_fallback(
        group,
        "keywords",
        use_repr=False,
        value_handler=partial(_keywords, separator=";"),
        separator="; ",
    )
    duplicate_ids = "; ".join(
        f"({item.filename},{item.Index})" for item in group.itertuples(name="Paper")
    )
    return pd.Series(
        {
            "source_database_indices": duplicate_ids,
            "title": group.loc[repr_idx, "title"],
            "authors": group.loc[repr_idx, "authors"],
            "keywords": keywords,
            "source": group.loc[repr_idx, "source"],
            "abstract": abstract,
            "doi": max((x for x in group["doi"]), key=len),
            "url": max((x for x in group["url"]), key=_url_relevance),
            "year": group.loc[repr_idx, "year"],
            "include": None,
        }
    )


def _merge_clusters(deduped_df):
    return deduped_df.groupby("cluster_id").apply(_merge_cluster)
