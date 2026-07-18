# Web of Science

**Type:** hybrid — the only backend that can act as either a console backend
or a live API backend, switched by the `use_starter_api` option.

```yaml
- name: Web of Science
  adapter: WebOfScienceDSLAdapter
  backend:
    type: WebOfScienceBackend
    options:
      api_key: ${MWF_SEARCH_CLARIVATE_API_KEY}
      use_starter_api: false
      save: false
      persistence_adapter: wos-api.csv
      db: WOS
      limit: 50
      page: 1
      sort_field: RS+D
```

## Two modes

| `use_starter_api` | Behavior |
|---|---|
| `false` (default in the example config) | Treated as a **console backend** by the CLI (`BackendSpec.is_console_backend`) — runs sequentially with ACM/IEEE Xplore, printing the query for manual use in the WoS UI. `save`/`persistence_adapter` are forced off regardless of what's configured. |
| `true` | Calls Clarivate's WoS Starter API directly (`clarivate.wos_starter.client.DocumentsApi.documents_get`), paginating via the `page` param, accumulating hits until an empty page is returned. |

Any extra keyword options besides `api_key`, `use_starter_api`, `save`, and
`persistence_adapter` (e.g. `db`, `limit`, `page`, `sort_field`) are passed
straight through to `DocumentsApi.documents_get(...)` as `**wos_call_params`.

## Output columns (starter API mode only)

`title`, `authors`, `document_type`, `source`, `keywords`.

!!! warning "Narrower schema than other backends"
    Unlike every other API backend, Web of Science's `DataFrame` does
    **not** include `abstract`, `doi`, `url`, or `year` — the starter API
    client library exposes a different document shape
    (`document.names.authors`, `document.types`, `document.source`,
    `document.keywords.author_keywords`) and no equivalent fields were wired
    up for those four columns. If downstream tooling (deduplication, metrics)
    expects a uniform schema across all backend CSVs, this is the backend to
    check first when something's missing.

## Adapter notes (`WebOfScienceDSLAdapter`)

- Uses `TI`, `AB`, `AK`, `DT`, `WC`, `LA`, `DOP`.
- Value maps: `evidence_type` `"article"` → `"Article"`; `subject`
  `"computer science"` → `"Computer Science"`; `language` `"english"` →
  `"English"`.
- Date handling is asymmetric: `after` becomes `lo/<today>`; `before`
  becomes a floor of `1950-01-01/hi`; `between` is a direct `lo/hi` range.
