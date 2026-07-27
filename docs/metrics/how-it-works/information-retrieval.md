---
title: How Information Retrieval Metrics Work
description: Learn how Metrics normalizes study identifiers and calculates set-based search-quality measures.
tags:
- metrics
- information-retrieval
---

# How Information Retrieval Metrics Work

The `search-quality` command treats a known-good retrieval set and a search-result set as two sets of study identifiers. It measures their overlap, not row order or repeated rows.

## Inputs and identifiers

Supply the known-good set with `-i`, then give the retrieved results as the positional file. Inputs may be CSV or `.xlsx`. The known-good input also needs the key column selected by `-k` (`id` by default), because shared inputs are loaded using that column.

The default comparison column is `doi`. To compare another identifier, or a composite identifier, repeat `-t` before the subcommand. This runnable example compares the canonical files by title:

```bash
uv run metrics -i docs/metrics/examples/information-retrieval/known-good.csv -t title search-quality docs/metrics/examples/information-retrieval/search-results.csv
```

For each row, the command trims leading and trailing whitespace and converts each comparison value to lower case. With several `-t` columns, it joins the normalized values with an underscore to make one comparison key.

!!! warning
    Do not use blank identifiers. Missing values become empty strings during normalization, and the command does not protect you from matching blank keys.

## Set comparison

After normalization, repeated identifiers collapse into one set member. The command counts:

- **true positives**: identifiers in both sets;
- **false positives**: identifiers returned by the search but absent from the known-good set; and
- **false negatives**: known-good identifiers absent from the search results.

This means the metrics describe unique normalized identifiers. They do not penalize duplicate rows, and they cannot detect that two different identifiers represent the same paper.

## Reported measures

| Measure | Calculation | Useful reading |
|---|---|---|
| Precision | true positives / retrieved identifiers | Of the unique studies returned, how many were known-good? |
| Recall | true positives / known-good identifiers | How much of the known-good set did the search retrieve? |
| F1 | harmonic mean of precision and recall | A single balance measure when precision and recall matter equally. |
| Jaccard | intersection / union | The fraction of all unique identifiers across both sets that overlap. |
| Dice | twice the intersection / sum of set sizes | Another overlap measure that gives the shared identifiers twice the weight. |

All five measures range from 0 to 1 and are printed as percentages. Higher values mean greater overlap under the selected identifier rule. A strong score only supports the coverage of the known-good set; it does not prove that the set is complete or that every retrieved study is relevant.
