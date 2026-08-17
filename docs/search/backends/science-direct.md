# ScienceDirect

**Type:** live API (`ScienceDirectBackend`), via Elsevier's metadata API.

```yaml
- name: ScienceDirect
  adapter: ScienceDirectDSLAdapter
  backend:
    type: ScienceDirectBackend
    options:
      api_key: ${MWF_SEARCH_ELSEVIER_API_KEY}
      csv_path: science_direct.csv
```

## Backend behavior

- Endpoint: `GET https://api.elsevier.com/content/metadata/article`, headers
  `X-ELS-APIKey` + `Accept: application/json`.
- `view=COMPLETE` requests the full metadata payload.
- Pagination: offset-based (`start`/`count`), page size 10, stops when
  `opensearch:itemsPerPage` reports 0.
- No built-in retry/backoff logic — a non-2xx response raises immediately
  (`response.raise_for_status()`).

## Constructor options

| Option     | Default      | Notes                                                                                                   |
| ---------- | ------------ | ------------------------------------------------------------------------------------------------------- |
| `api_key`  | — (required) | `MWF_SEARCH_ELSEVIER_API_KEY`                                                                           |
| `save`     | `True`       | Whether to persist results                                                                              |
| `csv_path` | `None`       | Resolved relative to the results directory (see [Configuration](../configuration/config-file.md)) |

## Output columns

`title`, `abstract`, `keywords`, `authors`, `source`, `url`, `doi`, `year`.

- `url` prefers a link from the response's `link` array; falls back to a
  constructed `https://doi.org/<doi>` if no link is present, or `"N/A"` if
  there's no DOI either.
- `year` is parsed from `available-online-date`.

## Adapter notes (`ScienceDirectDSLAdapter`)

- Splits output into a query string (`TITLE(...)`, `ABSTRACT(...)`, etc.) and
  filter clauses combined via `emit_query` into
  `(query) AND (filters)`-style syntax.
- `evidence_type` value map only covers `"article"` → `"JL"` — a
  `"conference"` clause passes through unmapped (see
  [Field mapping](../architecture/field-mapping.md)).
- Date bounds render as `PUB-DATE AFT/BEF 'YYYYMMDD'`; year-only bounds
  expand to the full calendar year.
