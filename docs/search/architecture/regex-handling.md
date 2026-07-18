# Regex handling

This mechanism adds client-side matching using regular expressions after
a backend has obtained the search results from a vendor database. The
requirement for such a functionality emerged because the basic Springer API
doesn't allow querying the `title` and `abstract` fields individually. This
is shortcoming is handled via declaring that specific fields are regex-only in
an adapter or by using the `match["regex"]("...")` syntax construct.

Those expressions are translated to their best regular expression similes,
and composed together, finally finding their way into the `QueryObject.regex`
field.

!!! note
    This functionality is _unstable_ mainly because not all boolean queries have
    an exact regular expression alternative. Use with care!

## Declaring a regex field

An adapter opts a field into this behavior by overriding `_is_regex_field`:

```python
class SpringerDSLAdapter(DSLAdapter):
    _UNSEARCHABLE_FIELDS = {"title", "abstract"}

    # override the base method that instructs the adapter how to interpret
    # whether the expression qualified with a given field must be
    # translated to a regular expression.
    def _is_regex_field(self, field: str) -> bool:
        return field in self._UNSEARCHABLE_FIELDS
```

Internally in the base `DSLAdapter`, every `adapt()` call for a node that can be
qualified (`ValueExpr`, `DateExpr`, `BinaryExpr`, `UnaryExpr`, `MatchExpr`,
`GroupExpr`) is routed through `_emit_node_with_regex_handling`, which:

1. Splits the node's applicable fields (its own `fields`, or the qualifier of
   the nearest surrounding scope) into **regex fields** and **passthrough fields**
   (`_handle_regex_fields`).
2. If there are passthrough fields (or the node had no field qualifier at all),
   node translation continues normally.
3. If _every_ field on the node is a regex field, the node's contribution to the
   final `.query` or `.filters` is dropped.
4. Either way, a regex pattern is computed (`_extract_regex_pattern`) and
   merged onto the result's `.regex` dict, keyed by field name.

## How the pattern itself is built

`_create_regex` walks the sub-tree rooted at the node (`__create_regex_inner`)
and builds two things:

- a **positive** trailing pattern (for a single literal or an `OR` of
  literals), and
- a list of **lookaheads**:
  - _positive_ lookaheads (`(?=.*...)`) are used to express `&` binary expressions.
  - _negative_ lookaheads (`(?!.*...)`) are used for negations.

In building the regular expressions, plain string values in the DSL are escaped
(using `re.escape`) and then DSL wildcards are translated: `*` -> `\w*`, `?` -> `\w?`,
`+` -> `.+`, and literal spaces -> `\s`.

The trailing pattern and the lookaheads are combined into a final regex per field.
This method of building up regular expressions yields good results for easy to
moderately complex queries. Complex boolean search queries might end up not being
well-formed.

`match[regex]("...")` nodes short-circuit this entirely — the user-supplied pattern
is used verbatim, unescaped.

## Examples

These are drawn directly from
`tests/mapwisefox/search/dsl/parser/test_regex_handling.py`, using a stub
adapter where only `regex_field` is marked as a regex field:

| DSL                                                              | Resulting query              | Resulting regex              |
| ---------------------------------------------------------------- | ---------------------------- | ---------------------------- |
| `"amazing" in regex_field`                                       | _(empty)_                    | `amazing`                    |
| `!"amazing" in regex_field`                                      | _(empty)_                    | `^(?!.*amazing)`             |
| `"amazing" in regex_field,normal`                                | `VAL(amazing in ['normal'])` | `amazing` (regex_field only) |
| `"amazing" in regex_field & "b" in normal`                       | `VAL(b in ['normal'])`       | `amazing`                    |
| `"a" in regex_field & (("b" in normal) \| ("c" in regex_field))` | `VAL(b in ['normal'])`       | `^(?=.*a)(?=.*c)`            |
| `"a" in regex_field & ("b" in normal \| !"c" in regex_field)`    | `VAL(b in ['normal'])`       | `^(?=.*a)(?!.*c)`            |
| `("a"\|"b") in regex_field & "c"`                                | `VAL(c)`                     | `(a\|b)`                     |
| `("a"\|("b"&"c")) in regex_field`                                | _(empty)_                    | `^(?=.*b)(?=.*c)a`           |
| `("a"\|(!"b"&!"c")) in regex_field`                              | _(empty)_                    | `^(?!.*b)(?!.*c)a`           |

Key takeaways from this table:

- **Mixed field lists split cleanly**: `"x" in regex_field, normal` produces
  _both_ a normal query clause for `normal` _and_ a regex entry for
  `regex_field` — nothing is lost, it just gets routed to two different
  outputs.
- **AND'd clauses become lookaheads, OR'd clauses become alternation** —
  this preserves boolean semantics in a single-pass regex rather than
  requiring multiple passes.
- **Negation becomes a negative lookahead** (`(?!.*...)`), never literal
  regex negation syntax, so it composes correctly alongside positive
  lookaheads.
- **A leading literal term outside of any AND/OR nesting stays as trailing
  positive match text** (e.g. `^(?=.*b)(?=.*c)a`), with lookaheads collected
  from nested groups placed before it.

## Handling of binary DSL expressions

When two already-adapted branches each carry a regex for the same field,
`emit_binary`'s default implementation merges them:

- `AND` -> both patterns become positive lookaheads and are concatenated:
  `^(?=.*left)(?=.*right)`.
- `OR` -> wrapped in a non-capturing alternation:
  `^(?:left|right)`.

## Practical implications

- There are fields **per-adapter** that require regex handling, not global —
  the same DSL field can be freely searchable in one vendor's adapter and
  regex-only in another's.
- It is the backend's responsibility to actually apply the resulting regular
  expressions. This allows the flexibility of choosing the text on which to
  apply the regular expressions and the regular expression flags.
- If you mark a field as regex-only, double check every adapter method that
  builds compound clauses (`emit_binary`, `emit_group`, `emit_query`) still
  produces something sensible when that field's contribution is empty.
- Combining verbatim regular expressions with generated regular expressions
  within the same field context is possible and allowed (e.g. for narrowing
  down the result set uniformly across backends on the client). Always check
  for unintended side-effects.
