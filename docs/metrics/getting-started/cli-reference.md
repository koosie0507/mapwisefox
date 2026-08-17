---
title: Metrics CLI Reference
description: Reference for the MapwiseFox Metrics command-line interface and its agreement and retrieval commands.
tags:
- metrics
- cli
---

# Metrics CLI Reference

Use the `metrics` Command Line Interface (CLI) to calculate search-quality and inter-rater measures. Invoke it from the repository root with `uv run metrics`; global options must appear before the subcommand.

```bash
uv run metrics --help
```

## Shared options

| Option | Meaning |
|---|---|
| `-i`, `--input-file` | Input file. Repeat it for each known-good, rater, or trusted-rater file. |
| `-t`, `--target-value` | Target column shared by the relevant files. Repeat it to calculate separate results for several columns. `search-quality` defaults to `doi` when you omit it. |
| `-k`, `--key-attr` | Record identifier column in every `-i` input. The default is `id`. |
| `-o`, `--output-file` | Optional `.xlsx` workbook for results. |
| `-x`, `--extra-column` | Optional column to include in kappa disagreement sheets. Repeat for more columns. |

Only CSV and `.xlsx` input files are supported. Use `.xlsx` for output workbooks.

## Commands

### `search-quality`

```text
metrics [global options] search-quality SEARCH_RESULTS_FILE
```

Compares `SEARCH_RESULTS_FILE` with every file supplied through `-i`. It prints precision, recall, F1, Jaccard, and Dice for each known-good file. It compares `doi` by default, or the column or columns supplied through `-t`. With `-o`, it writes a `Search Quality` worksheet.

### `kappa-score`

```text
metrics -i RATER_A -i RATER_B -t DECISION [global options] kappa-score [--agreement-labels LABELS]
```

Computes Cohen's kappa for **exactly two** input raters and each target column; supplying fewer or more than two `-i` files is rejected. The default labels are `include,exclude`; use `--agreement-labels` with a comma-separated replacement list when needed. With `-o`, it writes a `stats` worksheet plus one `disagreements on {target}` worksheet per target column. `-x` selects extra columns for those disagreement worksheets.

### `mae`

```text
metrics -i TRUSTED_RATER ... -t SCORE [global options] mae EVALUATED_RATER
```

Computes Mean Absolute Error (MAE) between the evaluated rater and the mean, minimum, and maximum trusted-rater scores. With `-o`, it writes a `Mean Absolute Error` worksheet.

### `rmse`

```text
metrics -i TRUSTED_RATER ... -t SCORE [global options] rmse EVALUATED_RATER
```

Computes Root Mean Squared Error (RMSE) against the same three trusted-rater summaries. With `-o`, it writes a `Root Mean Squared Error` worksheet.

### `lin-ccc`

```text
metrics -i TRUSTED_RATER ... -t SCORE [global options] lin-ccc EVALUATED_RATER
```

Computes Lin's Concordance Correlation Coefficient (CCC) against the mean, minimum, and maximum trusted-rater scores. With `-o`, it writes a `Lin CCC` worksheet.

### `icc`

```text
metrics -i TRUSTED_RATER ... -t SCORE [global options] icc EVALUATED_RATER
```

Computes `ICC(1,1)`, `ICC(2,1)`, and `ICC(3,1)` between the evaluated rater and trusted raters. With `-o`, it writes an `Intra-Class Correlation` worksheet.
