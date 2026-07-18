# ACM

**Type:** console-only. There is no `ACMBackend` class — the example config
runs `AcmDSLAdapter` through the generic `ConsoleBackend`, which prints the
translated query and any filters for you to paste into the ACM Digital
Library's advanced search UI by hand.

```yaml
- name: ACM
  adapter: AcmDSLAdapter
  backend: ConsoleBackend
```

## Adapter notes (`AcmDSLAdapter`)

- Query syntax: `Field:(...)`, e.g. `Title:("machine learning" AND "CNN")`.
- Supported fields: `title`, `abstract`, `keywords`, `published`,
  `evidence_type` — see [Field mapping](../architecture/field-mapping.md) for
  the full table. `language` and `subject` clauses are silently dropped (no
  field mapping exists for them).
- `evidence_type` and date ranges are always rendered as **filters**
  (`Article Type`, `E-Publication Date`), never as query text, regardless of
  whether they're wrapped in `[->filter: ...]` — `_FILTER_FIELDS =
  {"evidence_type", "language", "subject"}`.
- `evidence_type` values `"article"` and `"conference"` both map to ACM's
  single `"Research Article"` filter value — ACM doesn't distinguish them at
  the filter level the way other vendors do.
- Date filters use `MM/DD/YYYY` bounds inside `(lo TO hi)`; year-only bounds
  are expanded to the full year (`01/01/YYYY` through `12/31/YYYY`).

Since there's no API integration, there's no CSV output for this backend —
results come from manually running the printed query in ACM's own UI and
exporting from there.
