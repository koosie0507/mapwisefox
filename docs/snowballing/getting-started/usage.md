# Usage

This walkthrough creates a small Excel workbook, uses it for one level of
backward snowballing, and inspects the result. Run the commands from the
MapwiseFox repository root after completing the
[workspace setup](../../getting-started/installation.md).

The example starts from Wohlin's *Guidelines for snowballing in systematic
literature studies and a replication in software engineering*, which has DOI
`10.1145/2601248.2601268`.

## 1. Create the input workbook

Create `data/snowballing-example.xlsx` with a `Seeds` worksheet and an empty
`Excluded` worksheet:

```bash
uv run python - <<'PY'
from pathlib import Path

import pandas as pd

workbook = Path("data/snowballing-example.xlsx")
workbook.parent.mkdir(parents=True, exist_ok=True)

with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
    pd.DataFrame({"doi": ["10.1145/2601248.2601268"]}).to_excel(
        writer, sheet_name="Seeds", index=False
    )
    pd.DataFrame({"doi": []}).to_excel(
        writer, sheet_name="Excluded", index=False
    )
PY
```

The seed and exclusion worksheets must use the same DOI column. Its default
name is `doi`; use `--id-column-name` when a workbook uses another name.

DOIs may be bare identifiers or links such as
`https://doi.org/10.1145/2601248.2601268`. The command strips common DOI URL
prefixes, surrounding whitespace, and letter case before looking papers up.
Blank cells and duplicate DOIs are ignored.

## 2. Run backward snowballing

```bash
uv run snowball data/snowballing-example.xlsx \
  --sheet-name Seeds \
  --exclude Excluded
```

Backward snowballing is the default direction, and the default maximum depth
is one. This run retrieves the seed paper's references but does not expand the
references of those newly discovered papers.

The command uses Semantic Scholar over the network. Its coverage can change,
so the exact set of rows may differ between runs. If Semantic Scholar cannot
find the seed DOI, the command prints a warning and still creates a valid,
possibly empty result workbook.

## 3. Inspect the result

The output is written beside the input as
`data/snowballing-example-snowball.xlsx`. Backward results are placed in the
`Back` worksheet.

```bash
uv run python - <<'PY'
import pandas as pd

workbook = "data/snowballing-example-snowball.xlsx"
print(pd.ExcelFile(workbook).sheet_names)
print(
    pd.read_excel(workbook, sheet_name="Back")
    .loc[:, ["doi", "title", "year", "referencing_paper_ids"]]
    .head()
    .to_string(index=False)
)
PY
```

The result contains one row per discovered DOI, sorted by DOI:

| Column | Description |
|---|---|
| `cluster_id` | Zero-based output row index. It is not a stable paper ID or a deduplication cluster. |
| `doi` | Normalized DOI. |
| `title` | Paper title returned by Semantic Scholar. |
| `authors` | Semicolon-separated author names. |
| `abstract` | Abstract, when available. |
| `source` | Publication source, when available. |
| `url` | Canonical `https://doi.org/<doi>` link. |
| `year` | Publication year, when available. |
| `has_pdf` | Whether Semantic Scholar reports an available PDF. |
| `pdf_url` | PDF URL, when available. |
| `referencing_paper_ids` | Sorted, semicolon-separated DOIs directly linked to this result. In this backward example, these are papers that reference the result. |

The complete schema is written even when no papers are discovered. See the
[CLI reference](cli-reference.md) to run forward snowballing, traverse more
levels, change the output name, or write results into the input workbook.
