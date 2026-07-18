# IEEE Xplore

**Type:** console-only, same as ACM — no dedicated backend class exists
today; the example config runs `XploreDSLAdapter` through the generic
`ConsoleBackend`.

```yaml
- name: IEEE Xplore
  adapter: XploreDSLAdapter
  backend: ConsoleBackend
```

## Adapter notes (`XploreDSLAdapter`)

- Query syntax: `"Field":value`, quoting the value unless it contains a
  wildcard (`*`/`?`), e.g. `"Document Title":"machine learning"` vs.
  `"Author Keywords":tool*`.
- Supported fields: `title` (`Document Title`), `abstract`, `author`
  (`Authors`), `keywords` (`Author Keywords`), `affiliation`
  (`Author Affiliations`), `evidence_type` (`content_type`).
- `evidence_type` is **always** routed to `QueryObject.filters["content_type"]`
  rather than the query string — `_ALWAYS_FILTER_FIELDS = {"evidence_type"}`
  — because Xplore's UI/API takes content type as a separate facet, not a
  query term. Values map `"article"` → `Journals`, `"conference"` →
  `Conferences`.
- Date bounds map to `start_year`/`end_year` filter entries, not a query
  clause — Xplore has no `DateExpr` query syntax in this adapter.
- `language` and `subject` clauses are unsupported (no field mapping exists).

As with ACM, there's no live API call here — the printed query/filters are
meant to be entered into Xplore's own search UI manually.
