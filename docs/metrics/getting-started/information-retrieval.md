---
title: Information Retrieval Metrics
description: Compare a search-result set with known-good studies using precision, recall, and related set measures.
tags:
- metrics
- information-retrieval
- systematic-review
---

# Information Retrieval Metrics

Measure how well a search retrieves a known-good set of studies. This example compares CSV exports by DOI and prints precision, recall, F1, Jaccard, and Dice scores.

## Prepare the files

The known-good file at `docs/metrics/examples/information-retrieval/known-good.csv` must contain an `id` column and a `doi` column. The search-result file at `docs/metrics/examples/information-retrieval/search-results.csv` must contain a `doi` column. Use a stable, non-blank identifier for every row you want to compare.

The example data is supplied with the documentation. Replace these paths with your own repository-root-relative paths when you analyse a review. Both inputs may instead be CSV or `.xlsx` files.

!!! warning
    Do not leave comparison identifiers blank. Blank values are normalized and treated as values by the current command. They can therefore create a false match.

## Compare the sets

Run this command from the repository root. Global options, including `-i`, come before the `search-quality` subcommand.

```bash
uv run metrics -i docs/metrics/examples/information-retrieval/known-good.csv search-quality docs/metrics/examples/information-retrieval/search-results.csv
```

The canonical files produce this output:

```plaintext
known-good (columns: doi):
  Precision: 50.00%
  Recall:    66.67%
  F1:        57.14%
  Jaccard:   40.00%
  Dice:      57.14%
```

The command prints one labelled block for each known-good file. It reports the five scores as percentages. See [How it works](../how-it-works/information-retrieval.md) for their meaning and for comparison columns other than DOI.

## Save a workbook

Add `-o` before the subcommand to write the scores to an Excel workbook:

```bash
uv run metrics -i docs/metrics/examples/information-retrieval/known-good.csv -o search-quality.xlsx search-quality docs/metrics/examples/information-retrieval/search-results.csv
```

The workbook contains a `Search Quality` worksheet. It has one row per known-good input file and stores the scores as numeric values.
