# Springer

**Type:** live API (`SpringerBackend`), the only backend that combines a
server-side query with a **client-side regex post-filter**.

```yaml
- name: Springer
  adapter: SpringerDSLAdapter
  backend:
    type: SpringerBackend
    options:
      api_key: ${MWF_SEARCH_SPRINGER_API_KEY}
      csv_path: springer.csv
      fetch_all: true
```

## Backend behavior

- Endpoint: `GET https://api.springernature.com/meta/v2/json`.
- Pagination: page-size 25, computed offsets (`s = page * 25 + 1`), continues
  while `fetch_all=True` and fewer records than `result[0].total` have been
  collected.
- **Rate-limit handling**: on HTTP 429, retries up to 5 times with
  exponential backoff (`sleep(3 ** (retry_no + 1))` seconds); if retries are
  exhausted, it logs and proceeds with whatever was fetched so far rather
  than failing the whole run.
- **Post-retrieval regex filtering**: after fetching, results are filtered
  locally via `_local_filter`, which compiles every entry in
  `QueryObject.regex` (case-insensitive) and keeps a record if _any_
  compiled pattern matches the corresponding response field. This is what
  makes `title`/`abstract` searching work at all for Springer, since its API
  can't filter on those fields server-side — see
  [Regex handling](../architecture/regex-handling.md).

## Constructor options

| Option      | Default      | Notes                                                                                           |
| ----------- | ------------ | ----------------------------------------------------------------------------------------------- |
| `api_key`   | — (required) | `MWF_SEARCH_SPRINGER_API_KEY`                                                                   |
| `csv_path`  | `None`       | If set, `save_result` is automatically `True`; resolved relative to the results directory |
| `fetch_all` | `True`       | Set `False` to fetch only the first page                                                        |

## Output columns

`title`, `abstract`, `keywords`, `authors`, `source`, `doi`, `url`, `year`.

- `url` prefers an `html`-format URL; falls back to `https://doi.org/<doi>`,
  or `"N/A"`.
- `year` is parsed from `publicationDate`.

## Adapter notes (`SpringerDSLAdapter`)

- `title` and `abstract` are declared regex-only
  (`_UNSEARCHABLE_FIELDS = {"title", "abstract"}`) — clauses on these fields
  never appear in the query string, only in `QueryObject.regex`.
- `evidence_type` maps both `"article"` and `"conference"` to `"Journal"`.
- **Premium fields**: the adapter takes an `is_premium: bool` constructor
  flag. When `False` (the default), a large set of fields
  (`_PREMIUM_FIELDS`, including `subject`/`discipline`, `language`, and
  several Springer-specific facets) are excluded from
  `_is_field_supported`, so clauses on them are silently dropped rather than
  sent to the API. Set `is_premium: true` in `adapter_options` if your
  Springer account has premium API access.
- Date bounds render as `datefrom:"..."`/`dateto:"..."` filter clauses.
