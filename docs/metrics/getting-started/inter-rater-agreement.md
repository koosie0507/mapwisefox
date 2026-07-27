---
title: Inter-Rater Agreement
description: Compare screening decisions or quality-assessment scores from systematic-review raters.
tags:
  - metrics
  - inter-rater-agreement
  - systematic-review
---

# Inter-Rater Agreement

Check whether two screeners reach similar discrete decisions, or assess one rater's continuous quality scores against trusted raters. The commands match records through a shared `id` column.

## Screen with two raters

For Cohen's kappa, each file must contain `id` and `decision` columns. This workflow compares exactly two raters. The default decision labels are `include` and `exclude`.

```bash
uv run metrics -i docs/metrics/examples/inter-rater-agreement/screener-a.csv -i docs/metrics/examples/inter-rater-agreement/screener-b.csv -t decision kappa-score
```

The supplied files produce a kappa of `0.50`, which the command labels `moderate agreement`:

```plaintext
The Cohen Kappa agreement score between screener-a and screener-b on 'decision' is 0.50: [moderate agreement]
```

The order of the two `-i` files sets the left and right rater names in the printed result and any disagreement report. The command compares only records with a shared `id` and a non-missing decision from both raters.

If your data uses different labels, pass their complete comma-separated list after `kappa-score`. For example, use `--agreement-labels yes,no` only with files whose decision values are `yes` and `no`; the supplied files use `include` and `exclude`.

## Assess continuous scores

For quality assessment using numeric scores (e.g. ratings from 1 to 10), give one or more trusted-rater files with `-i`. Then, give another rater that is being evaluated against those trusted raters the final positional file. All files need `id` and the numeric target column named with `-t`; these examples use `score`.

```bash
uv run metrics -i docs/metrics/examples/inter-rater-agreement/trusted-rater-a.csv -i docs/metrics/examples/inter-rater-agreement/trusted-rater-b.csv -t score mae docs/metrics/examples/inter-rater-agreement/evaluated-rater.csv

uv run metrics -i docs/metrics/examples/inter-rater-agreement/trusted-rater-a.csv -i docs/metrics/examples/inter-rater-agreement/trusted-rater-b.csv -t score rmse docs/metrics/examples/inter-rater-agreement/evaluated-rater.csv

uv run metrics -i docs/metrics/examples/inter-rater-agreement/trusted-rater-a.csv -i docs/metrics/examples/inter-rater-agreement/trusted-rater-b.csv -t score lin-ccc docs/metrics/examples/inter-rater-agreement/evaluated-rater.csv

uv run metrics -i docs/metrics/examples/inter-rater-agreement/trusted-rater-a.csv -i docs/metrics/examples/inter-rater-agreement/trusted-rater-b.csv -t score icc docs/metrics/examples/inter-rater-agreement/evaluated-rater.csv
```

The first three commands compare the evaluated score with the trusted raters' mean, minimum, and maximum scores for each record. `icc` instead includes the evaluated rater with the trusted raters. Keep the same trusted files and their order across runs for a reproducible audit trail.

## Save optional Excel output

Place `-o` with the global options, before the subcommand. A kappa workbook has a `stats` sheet and a disagreement sheet for each target column. Each continuous command writes its results to one named worksheet. You can reuse a `.xlsx` workbook to collect those continuous worksheets.

```bash
uv run metrics -i docs/metrics/examples/inter-rater-agreement/trusted-rater-a.csv -i docs/metrics/examples/inter-rater-agreement/trusted-rater-b.csv -t score -o agreement-metrics.xlsx rmse docs/metrics/examples/inter-rater-agreement/evaluated-rater.csv
```

Read [How it works](../how-it-works/inter-rater-agreement.md) before interpreting a score as evidence of acceptable agreement.
