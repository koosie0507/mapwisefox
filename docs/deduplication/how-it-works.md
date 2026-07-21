# How it works

`deduplicate` is a thin, opinionated wrapper around the
[`dedupe`](https://docs.dedupe.io/en/latest/index.html) library. This page
covers what our wrapper does and why — for the mechanics of the underlying
library (blocking, variable types, active learning internals, threshold
tuning), the [dedupe.io docs](https://docs.dedupe.io/en/latest/index.html)
are the reference; we won't repeat them here.

## Everything gets lumped into one pool first

Every `.csv`/`.bib` file in `--input-dir` is loaded, normalized to a common
structure, and concatenated into a single dataset **before** matching
starts. `deduplicate` doesn't track which source each record came from —
it just looks for near-duplicates across the combined pool.

## Input normalization

- `.bib` files: parsed generically (`title`, `abstract`, `author`,
  `keywords`, `booktitle`/`journal`, `year`, `doi`, `url`) — filename doesn't
  matter.
- `.csv` files: assumed to already have the target columns (`title`,
  `abstract`, `authors`, `keywords`, `source`, `year`, `doi`, `url`), **except**
  for the filenames `wos.csv`, `xplore.csv`, and `ieee.csv`, which are
  remapped from the raw column headers used by the Web of Science and IEEE
  Xplore web UI exports (e.g. `"Article Title"` → `title`).

## Matching fields

Records are compared on four fields: `title`, `authors`, `source`, and
`keywords` (`abstract`, `doi`, `url`, and `year` are carried along as
metadata but don't influence matching). All field values are lowercased and
stripped of surrounding quotes/whitespace before comparison. See dedupe.io's
[variable definition docs](https://docs.dedupe.io/en/latest/Variable-definition.html)
if you're curious about other comparison strategies.

## The dedupe config

Matching requires a trained model, and training requires labeled examples of
"these two records are/aren't the same study." Rather than asking you to
label examples every single run, `deduplicate` keeps a **dedupe config**,
consisting in two files inside `--dd-config-dir` (default `./dedupe`):

- `settings.dedupe`: a trained model, ready to use as-is.
- `training.json`: the labeled example pairs behind it, in case the model
  needs retraining later.

Existing configurations can be loaded directly and used as-is without requiring
labeling or training.

When no configuration exists yet, `deduplicate` drops you into an interactive 
terminal session ([`dedupe.console_label`](https://docs.dedupe.io/en/latest/API-documentation.html#dedupe.Dedupe.console_label)), asking you to confirm or
reject candidate duplicate pairs, trains a model from your answers, and saves
both files to `--dd-config-dir` for next time.

In practice this means **one config per query**: the labeled examples and
trained model for an entity resolution search don't transfer meaningfully to
a search on, say, renewable energy policy. Point `--dd-config-dir` at a
fresh, empty directory whenever you start a genuinely different review, and
reuse an existing one for reproducing previous results. 

## Threshold and clustering

Once a model is available, records are clustered with
[`partition()`](https://docs.dedupe.io/en/latest/API-documentation.html#dedupe.Dedupe.partition)
at the similarity score given by `--threshold` (default `0.5`) — pairs
scoring at or above that value end up in the same cluster. Raise it to be
more conservative about merging (fewer false-positive merges, more
near-duplicates left unmerged); lower it to merge more aggressively. See
dedupe.io's [guide to choosing a threshold](https://docs.dedupe.io/en/latest/Choosing-a-good-threshold.html)
for a deeper discussion of the tradeoff.

## Merging a cluster into one record

Each cluster becomes a single output row:

- `title`, `authors`, `source`, `abstract`, `year` — taken from whichever
  record in the cluster had the highest match confidence.
- `keywords` — the union of every record's keywords in the cluster.
- `doi` — the longest `doi` string found (a crude but effective way to
  prefer a fully-qualified DOI over a truncated or missing one).
- `url` — the most relevant URL, preferring a `doi.org` link over any other,
  and any real URL over `"N/A"`.
- `include` — always left empty; it's a placeholder column for a human
  reviewer to fill in during manual screening.
