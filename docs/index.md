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

Contributing tool documentation is highly encouraged.
