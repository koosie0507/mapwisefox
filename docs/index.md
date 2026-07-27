---
title: MapwiseFox
description: Tools for systematic literature reviews and systematic mapping studies.
tags:
- systematic-review
---

# MapwiseFox

MapwiseFox is a suite of tools for building and running systematic literature
reviews: searching multiple academic databases with a single query, deduplicating
and screening results, and tracking evidence through a review pipeline.

New to the repo? Start with [Getting Started](getting-started/installation.md)
for the workspace-wide setup (cloning, `uv sync`, shared `.env` conventions).

Each tool in the suite is documented here:

- **[Search](search/index.md)** — search multiple databases at once with a CLI backed
  by a single DSL that compiles down to vendor-specific query syntax for ACM, IEEE
  Xplore, ScienceDirect, Scopus, Springer, and Web of Science.
- **[Snowballing](snowballing/index.md)** — expand a set of known papers by following
 their references or citations through Semantic Scholar, with Excel workbooks as
 input and output.
- **[Metrics](metrics/index.md)** — measure search retrieval quality and agreement
  between screening or quality-assessment raters.
- **[Web](web/index.md)** — import an Excel primary-study list, screen evidence in
  a browser, and track include or exclude decisions.

Contributing tool documentation is highly encouraged.
