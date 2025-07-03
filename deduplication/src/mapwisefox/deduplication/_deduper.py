from os import access, R_OK
from pathlib import Path

import dedupe
import pandas as pd
from dedupe import variables as v


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


def _setup_deduper(dedupe_data, settings_file, training_file):
    fields = [
        v.String("title"),
        v.String("authors"),
        v.String("source"),
        v.String("keywords"),
    ]
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


def _run_dedupe(df, training_file, settings_file):
    dedupe_df = df.copy()
    dedupe_df.reset_index(drop=True, inplace=True)
    print("load input...")
    dedupe_data = _load_dedupe_data(dedupe_df)
    print("blocking and indexing...")
    deduper = _setup_deduper(dedupe_data, settings_file, training_file)
    print("matching & clustering...")
    clustered_dupes = deduper.partition(dedupe_data, 0.5)
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


def _merge_cluster(group):
    representative = group.loc[group["confidence"].idxmax()]
    all_keys = set(
        key.lower().strip() for keys in group["keywords"] for key in keys.split(";")
    )
    return pd.Series(
        {
            "title": representative["title"],
            "authors": representative["authors"],
            "keywords": ";".join(all_keys),
            "source": representative["source"],
            "abstract": representative["abstract"],
            "doi": max((x for x in group["doi"]), key=len),
            "url": max((x for x in group["url"]), key=_url_relevance),
            "year": representative["year"],
            "include": None,
        }
    )


def _merge_clusters(deduped_df):
    return deduped_df.groupby("cluster_id").apply(_merge_cluster)
