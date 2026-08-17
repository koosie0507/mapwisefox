# Usage

The `deduplicate` command reads all `.csv` and `.bib` files located in an input
directory, converts the data records from those files to an internal schema,
adds them all to the same pool, deduplicates them and writes the output to an
Excel spreadsheet.

## Input

`deduplicate` doesn't care whether a result file was produced by the Mapwisefox
[`search`](../../search/index.md) command, downloaded by hand from a vendor's own web
UI, or hand-crafted. The important thing is that it has the right shape:

- **`.bib` files** are parsed with a standard BibTeX parser, regardless of
  filename. Any well-formed BibTeX export works.
- **`.csv` files** are expected to have the following columns: `title`,
  `abstract`, `authors`, `keywords`, `source`, `year`, `doi`, `url`. This
  is the column set produced by `search`'s ScienceDirect, Scopus, and Springer
  backends - so their CSV output can be dropped in as-is.

!!! note
Files named `wos.csv`, `xplore.csv`, and `ieee.csv` get special handling.
These filenames trigger a header remap tailored to the raw exports you get
from the Web of Science and IEEE Xplore web UIs (different column names
entirely) — see [How it works](../how-it-works.md#input-normalization) for the mapping.

## Output

The output is an Excel workbook containing one sheet. The records in this sheet
are the deduplicated records. In addition to the input columns, the sheet
contains two important columns:

* **`cluster_id`**: the unique ID assigned by `deduplicate` to a cluster of
  duplicate papers (essentially, this is a unique paper ID);
* **`include`**: a new, empty column that will determine whether the paper
  should be selected for review or not. The existence of this column makes the
  spreadsheet directly usable in the `mapwisefox.web` interactive selection
  form.

## Usage example: ACM (BibTeX) + Scopus (CSV)

This is a common combination in practice: ACM has no live API backend, so you
run its query by hand and export BibTeX from the ACM Digital Library UI,
while Scopus results come straight from a live API call.

1. Run `search` with ACM on `ConsoleBackend` (to get a copy-paste query) and
   Scopus on its live backend:

   ```yaml
   query: |
     "entity resolution" in title,abstract

   backends:
     - name: ACM
       adapter: AcmDSLAdapter
       backend: ConsoleBackend

     - name: Scopus
       adapter: ScopusDSLAdapter
       backend:
         type: ScopusBackend
         options:
           api_key: ${MWF_SEARCH_ELSEVIER_API_KEY}
           csv_path: scopus.csv
   ```

   ```bash
   uv run search --config myconfig.yaml
   ```

   See [Search → Installation](../../search/getting-started/installation.md#api-keys)
   for how to set `MWF_SEARCH_ELSEVIER_API_KEY`. `scopus.csv` lands in
   `search`'s results directory (e.g. `data/search-results/`).

2. Paste the ACM query printed to your terminal into the ACM Digital
   Library's search UI, run it there, and use its **Export Citations →
   BibTeX** option to save `acm.bib`.

3. Put both files in `deduplicate`'s input directory (`./data/input` by
   default):

   ```bash
   mkdir -p data/input
   cp data/search-results/20260720/scopus.csv data/input/
   cp ~/Downloads/acm.bib data/input/
   ```

4. Run `deduplicate`:

   ```bash
   uv run deduplicate
   ```

   On the very first run, no dedupe config exists yet, so `deduplicate` drops
   you into an interactive labeling session in your terminal. It shows pairs
   of candidate records and asks whether they're the same study. See
   [How it works](../how-it-works.md#the-dedupe-config) for what this does and how to reuse the result on future
   runs.

5. The merged, deduplicated result is written to
   `./data/output/<timestamp>-deduplicated-records.xlsx` by default (pass
   `--output-file` to write somewhere else), sheet `all`, with one row per
   cluster:

   | Column | Description |
      |---|---|
   | `title`, `authors`, `source`, `abstract`, `year` | Taken from the most confident record in the cluster |
   | `keywords` | Union of all keywords across the cluster |
   | `doi` | The longest `doi` string in the cluster |
   | `url` | The most relevant URL in the cluster (a `doi.org` link is preferred) |
   | `include` | Left empty — for a human reviewer to mark inclusion/exclusion downstream |

See the [CLI reference](cli-reference.md) for all options, including how to point at a
different input directory or output file, reuse or reset the dedupe config, and
tune the matching threshold.
