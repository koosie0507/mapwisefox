---
title: Split workload usage
description: Assign a selected-study workbook to several independent quality-assessment reviewers.
tags:
- systematic-review
- quality-assessment
- workload-assignment
---

# Usage

Create independent quality-assessment workbooks for three reviewers. In this
example, each study is assigned to two reviewers so you can compare their scores.

## Prepare the selection workbook

Start with an Excel selection workbook, such as a reviewed output from
[`deduplicate`](../../deduplication/index.md). Each row represents one study.
If your studies are on a named worksheet, record its name for the command.

Create a criteria JSON file using the same format as the Assistant's
[Study QA configuration](../../assistant/getting-started/usage.md#study-qa).
This is the shipped example configuration:

```json title="criteria.json"
--8<-- "assistant/examples/study-qa-config.json"
```

## Create reviewer workbooks

Run `for-evaluation` with three evaluators and two evaluations per study:

```bash
uv run split-workload for-evaluation \
  data/output/selected-studies.xlsx \
  --evaluator-count 3 \
  --evaluation-count 2 \
  --evaluation-criteria-config criteria.json
```

Each study goes to exactly two different reviewers. The reviewer workloads are
balanced as closely as possible. When an equal division is not possible, their
study counts differ by no more than one.

The command writes one workbook for each reviewer beside the selection file:

```plaintext
data/output/YYYYMMDD-evaluator01.xlsx
data/output/YYYYMMDD-evaluator02.xlsx
data/output/YYYYMMDD-evaluator03.xlsx
```

Each workbook contains the assigned study rows. It also has a score column for
each `label` in `criteria.json`. Give each reviewer their own workbook, then
combine their completed assessments with your review process.

!!! tip
    Use `--worksheet-name "Studies"` when the selection workbook does not use
    its first worksheet for the study list.

For non-overlapping screening bundles, use
[`simple`](cli-reference.md#simple) instead.
