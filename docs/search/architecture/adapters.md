# Adapters

`DSLAdapter` (in `dsl/adapters/_base.py`) is an abstract base class that
implements the IR-walking machinery once, so each vendor-specific subclass
only needs to supply vendor knowledge: field names, value mappings, and
string formatting.

## The dispatch mechanism

`adapt()` is a `functools.singledispatchmethod` registered per IR node type
(`Query`, `ValueExpr`, `DateExpr`, `BinaryExpr`, `UnaryExpr`, `MatchExpr`,
`GroupExpr`, `OutputSpecExpr`). Each registered handler either:

- calls one of the `emit_*` hook methods directly (subclasses override
  these), or
- wraps that call with `_emit_node_with_regex_handling`, which intercepts
  fields flagged as "regex fields" for this adapter (see
  [Regex handling](regex-handling.md)) before falling through to the normal
  `emit_*` logic.

`GroupExpr`, `UnaryExpr`, and `MatchExpr` handlers also push the node's
`fields` onto `_field_ctx_stack` via `_scoped_fields()`, so nested `emit_*`
calls can read the enclosing field scope through the `field_ctx` property
without threading it through every method signature. `OutputSpecExpr`
similarly pushes onto `_output_ctx_stack`, readable via `output_ctx`.

## Hooks you override

| Method                                        | Required?          | Purpose                                                                                                                                                                                                                       |
| --------------------------------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `emit_value(node: ValueExpr)`                 | **Yes** (abstract) | Render a leaf string value, honoring `node.fields` / `field_ctx`.                                                                                                                                                             |
| `emit_date(node: DateExpr)`                   | **Yes** (abstract) | Render a date range/bound in vendor syntax.                                                                                                                                                                                   |
| `emit_binary(node)`                           | No (has a default) | Combine two already-adapted `QueryObject`s with AND/OR. Override when a vendor needs special query-vs-filter merging (most adapters that support the query/filter split override this — see ACM, ScienceDirect, Scopus, WoS). |
| `emit_not(node)`                              | No                 | Negation formatting; default calls `_format_negation` on the query string.                                                                                                                                                    |
| `emit_approx` / `emit_nearest` / `emit_match` | No                 | See [Operators](../dsl/operators.md) — defaults are pass-through except `match[regex]`.                                                                                                                                       |
| `emit_group(node)`                            | No                 | Parenthesization of a sub-expression; override to also push field scoping (see ACM, Scopus).                                                                                                                                  |
| `emit_query(ast_root)`                        | No                 | Top-level entry point — normalizes the whole tree and assembles the final query string from `.query` + `.filters`. Nearly every adapter overrides this to control exactly how filters get combined with the free-text query.  |

## Configuration hooks (field/value mapping)

| Method/attribute                                     | Purpose                                                                                                                                                                                                                                        |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `_FIELD_MAP: dict[str, str]`                         | DSL field name → vendor field name. Convention, not enforced by the base class.                                                                                                                                                                |
| `_VALUE_MAP: dict[str, dict[str, str]]`              | Per-field value translation (e.g. DSL `"article"` becomes `"Research Article"` on ACM). Convention.                                                                                                                                                   |
| `_map_field_name(field)`                             | Classmethod hook most adapters implement as `cls._FIELD_MAP.get(field, field)`.                                                                                                                                                                |
| `_is_field_supported(field)`                         | Whether a field is recognized at all by this adapter.                                                                                                                                                                                          |
| `_is_query_field(field)` / `_is_filter_field(field)` | Whether a field should render into the query string vs. `QueryObject.filters`. Both default to using `_is_field_supported`; override to route specific fields (e.g. `AcmDSLAdapter._FILTER_FIELDS`, `XploreDSLAdapter._ALWAYS_FILTER_FIELDS`). |
| `_enclose_field(field, query)`                       | How to wrap a rendered clause with its field name (`"field:(...)"`, `"field=(...)"`, `"FIELD(...)"`, etc. — every vendor's syntax differs here).                                                                                               |
| `_is_regex_field(field)`                             | Whether this field must always be treated as client-side regex rather than ever sent to the vendor (see [Regex handling](regex-handling.md)).                                                                                                  |

## Recipe: adding a new backend

1. **Create the adapter** in `dsl/adapters/_yourvendor.py`, subclassing
   `DSLAdapter`.
2. Define `_FIELD_MAP` (and `_VALUE_MAP` if the vendor uses different literal
   values for things like document type).
3. Implement `emit_value` and `emit_date` at minimum — look at an adapter for
   a vendor with similar query semantics as a starting template (e.g. Scopus
   and WoS are structurally similar; ScienceDirect and WoS both split
   query/filter output the same way).
4. Override `emit_binary`, `emit_group`, and `emit_query` if the vendor
   distinguishes free-text query from structured filters (most do).
5. Implement `_enclose_field` for the vendor's field-wrapping syntax.
6. Register the adapter in `dsl/adapters/__init__.py` (`__all__`) — this is
   what makes it addressable by name (`adapter: YourVendorDSLAdapter`) from a
   YAML config, via the lookup in `_config.py`.
7. Write tests mirroring `tests/mapwisefox/search/dsl/adapters/test_*.py`:
   a handful of `test_sanity_check`-style parametrized cases, plus one
   `test_ersa_query` run against the shared `ersa_query_text` fixture — this
   is the best regression net across the whole adapter surface at once.
8. Create the matching `SearchBackend` subclass in `backends/` (see
   [Backends](../backends/overview.md)) and register it in
   `backends/__init__.py`.
9. Add an example entry to `config.example.yaml`.
