# Scopus

**Type:** live API (`ScopusBackend`), via Elsevier's Scopus Search API.

```yaml
- name: Scopus
  adapter: ScopusDSLAdapter
  backend:
    type: ScopusBackend
    options:
      api_key: ${MWF_SEARCH_ELSEVIER_API_KEY}
      csv_path: scopus.csv
```

## Backend behavior

- Endpoint: `GET https://api.elsevier.com/content/search/scopus`, headers
  `X-ELS-APIKey` + `Accept: application/json`, `view=COMPLETE`.
- Pagination: cursor-based (`cursor=*` to start, then
  `search-results.cursor.@next`), continues while `fetch_all=True` and the
  cursor keeps advancing with non-empty hits.
- Prints progress (`fetched / total records fetched`) to stdout as it pages.

## Constructor options

| Option      | Default      | Notes                                            |
| ----------- | ------------ | ------------------------------------------------ |
| `api_key`   | — (required) | `MWF_SEARCH_ELSEVIER_API_KEY`                    |
| `save`      | `True`       | Whether to persist results                       |
| `csv_path`  | `None`       | Resolved relative to the dated results directory |
| `fetch_all` | `True`       | Set `False` to fetch only the first page         |

## Output columns

`title`, `abstract`, `keywords`, `authors`, `source`, `doi`, `url`, `year`.

- `authors` joins `given-name, surname` pairs.
- `url` prefers a `full-text` link relation; falls back to
  `https://doi.org/<doi>`, or `"N/A"`.
- `year` is parsed from `prism:coverDate`.

## Adapter notes (`ScopusDSLAdapter`)

- Uses `TITLE`, `ABS`, `AUTHKEY`, `AUTH`, `AFFIL`, `DOCTYPE`, `LANGUAGE`,
  `SUBJAREA`, `PUBYEAR`.
- **Field collapsing**: `title, abstract` → `TITLE-ABS`; `title, abstract,
keywords` → `TITLE-ABS-KEY` (see
  [Field mapping](../architecture/field-mapping.md)).
- `evidence_type` maps `"article"` → `ar`, `"conference"` → `cp`; any other
  value (e.g. a hypothetical `"book"`) is simply absent from the map and
  passed through unmapped.
- `subject` maps `"computer science"` → `COMP`; no mapping exists for
  `language` values — they pass through as-is.
- Date bounds use strict Scopus `AFT`/`BEF` semantics: because Scopus treats
  these as strict inequalities, year-only bounds are widened by **one extra
  year on each side** (e.g. `between "2010" and "2025"` becomes
  `AFT 2009 AND BEF 2026`) to avoid excluding the boundary years themselves.
