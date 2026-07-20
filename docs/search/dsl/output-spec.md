# Output spec

```
[->query: <expr>]
[->filter: <expr>]
```

Not every vendor search API treats every clause as free-text query terms.
Some clauses — document type, language, subject area, publication date — are
better expressed as structured **filters** than as query string fragments.
The rationale involves one of two cases:

* the *vendor's UI/API expects* them that way
* it's clearer to keep "what am I searching for" separate from "how am I
  narrowing the result set." as a matter of *personal preference*.

`[->filter: ...]` tells adapters: render this sub-expression's leaf values as
filter entries (`QueryObject.filters`) rather than as part of the query
string, wherever the target adapter supports doing so for that field.
`[->query: ...]` is the default. When explicit, it forces query-string
rendering for all fields that aren't deliberately marked as filter-only by
an adapter implementation.

## Field support varies by adapter

Whether a given field can actually be routed to the requested output depends on
the adapter's `_is_filter_field`/`_is_query_field` overrides (see
[Architecture → Field mapping](../architecture/field-mapping.md)). For
example:

- `AcmDSLAdapter._FILTER_FIELDS = {"evidence_type", "language", "subject"}` —
  these plus anything matched by the date-filter logic become ACM filters;
  everything else stays in the query string as long as the explicit filter output
  specifier isn't used.
- `XploreDSLAdapter._ALWAYS_FILTER_FIELDS = {"evidence_type"}` — `evidence_type`
  is *always* rendered as a filter for Xplore, output-spec or not, because
  Xplore's API takes it as a separate `content_type` parameter regardless.

So `[->filter: ...]` is a hint honored per-field per-adapter, not an
unconditional override — check the target adapter if a field isn't ending up
where you expect.

## Example

From the running example query:

```
[->filter: "english" in language & ("article" | "conference") in evidence_type & "computer science" in subject & published between "2010" and "2025"]
```

For `AcmDSLAdapter`, this yields (in `QueryObject.filters`):

```python
{"Article Type": ["Research Article"], "E-Publication Date": ["(01/01/2010 TO 12/31/2025)"]}
```

Note that `language` and `subject` are silently dropped by the ACM adapter's
`_FIELD_MAP` (ACM has no field mapping for them at all) — they simply don't
appear in the output. This is a good example of why it's worth checking each
[backend's page](../backends/overview.md) for field coverage before assuming
a filter clause will show up everywhere.
