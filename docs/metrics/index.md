---
title: Metrics
description: Measure search retrieval quality and agreement between systematic-review raters.
tags:
- metrics
- systematic-review
---

# Metrics

Use `metrics` to assess two important parts of a systematic literature review: whether a search retrieves known studies, and whether reviewers give consistent decisions or scores. It reads review data from CSV or Excel workbooks and prints results that you can also save to Excel.

## Choose a workflow

- **[Information retrieval](getting-started/information-retrieval.md)** compares a search-result set with a known-good set of studies.
- **[Inter-rater agreement](getting-started/inter-rater-agreement.md)** compares two screening raters or evaluates quality scores using trusted raters.

Run the examples from the repository root after completing the shared [installation steps](../getting-started/installation.md). Each command uses `uv run metrics`, so it runs the workspace version of the package.

## Learn more

- Read the [CLI reference](getting-started/cli-reference.md) for every command and shared option.
- Read [how information-retrieval scores work](how-it-works/information-retrieval.md) before comparing exported search results.
- Read [how inter-rater measures work](how-it-works/inter-rater-agreement.md) before drawing conclusions from agreement scores.
