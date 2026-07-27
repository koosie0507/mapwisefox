---
title: Split workload CLI reference
description: Reference for the split-workload simple and for-evaluation commands.
tags:
- command-line
- workload-assignment
---

# CLI reference

`split-workload` is a Command Line Interface (CLI) command group for dividing
Excel study workbooks. View its commands with:

```bash
uv run split-workload --help
```

## `simple`

`simple` finds matching `.xlsx` workbooks in an input directory. It randomizes
their rows and creates non-overlapping bundles. Every input workbook must have
a `cluster_id` column.

```bash
uv run split-workload simple --help
```

| Option | Default | Description |
|---|---|---|
| `--input-dir`, `-D` | `./data/output` | Directory that contains input workbooks. |
| `--include`, `-I` | `*-deduplicated-records.xlsx` | Filename pattern for input `.xlsx` workbooks. |
| `--split-count`, `-n` | `2` | Number of non-overlapping bundles to create for each matching workbook. |

For an input named `reviews.xlsx`, bundles are written below the input directory:

```plaintext
<input-dir>/splits/reviews/0001.xlsx
<input-dir>/splits/reviews/0002.xlsx
```

## `for-evaluation`

`for-evaluation` distributes the rows of one selection workbook for independent
evaluation. Each study is assigned to exactly `k` distinct evaluators among `n`
evaluators. Reviewer workloads can be uneven, but differ by no more than one.

```bash
uv run split-workload for-evaluation --help
```

| Argument or option | Default | Description |
|---|---|---|
| `SELECTION` | required | Input `.xlsx` selection workbook. |
| `--evaluator-count`, `-n` | required | Number of evaluators (`n`). |
| `--evaluation-count`, `-k` | required | Evaluations per study (`k`). It must satisfy `1 <= k <= n`. |
| `--worksheet-name`, `-w` | first worksheet | Worksheet containing the study rows. |
| `--evaluation-criteria-config`, `-c` | — | Optional Assistant Study QA criteria JSON file. Its criterion `label` values become score columns. |

The command writes `YYYYMMDD-evaluatorNN.xlsx` files next to `SELECTION`, one
per evaluator. See [Usage](usage.md) for a criteria file and a complete command.
