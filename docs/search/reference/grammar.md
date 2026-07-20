# Grammar reference

The DSL grammar, in full (`search/src/mapwisefox/search/dsl/parser/grammar.lark`):

```lark
--8<-- "search/src/mapwisefox/search/dsl/parser/grammar.lark"
```

## Rule-by-rule notes

- **`start` / `expr`** -- an expression is either an `output_spec_expr`
  (`[->query:...]`/`[->filter:...]`) or a `compound_expr`. Output specs
  can't be nested.
- **`compound_expr`** -- any of `group_expr`, `binary_expr`, `unary_expr`,
  `match_expr`, `date_expr`, or `value_expr`, optionally followed by an
  `attr_clause` (`in field_list`). The transformer (`_parser.py`,
  `compound_expr` method) attaches the parsed field list to the inner
  node's `.fields` attribute and then discards the `attr_clause` wrapper,
  which isn't instantiated in the final IR (see
  [Architecture → IR](../architecture/ir.md)).
- **`date_expr`** — three alternatives (`date_between`/`date_after`/
  `date_before`), each producing a `DateExpr` node directly in the
  transformer rather than going through `create_transformer`'s generic
  per-rule dispatch, since the same `DateExpr` class serves all three date
  operators (see [DSL → Dates](../dsl/dates.md)).
- **`match_op`** — three shapes (`approx`, `nearest[N]`, `match[type]`),
  parsed by a custom `match_op` transformer method rather than an
  auto-generated one, since the argument shape differs per case (see
  [DSL → Operators](../dsl/operators.md)).
- **`field_name`** — a bare `CNAME`, i.e. an identifier with no dedicated
  keyword list at the grammar level. Whether a given field name means
  anything is entirely up to the adapter it's fed to — the grammar itself
  accepts any identifier.
- **LALR parsing** — `Parser` builds the grammar with `parser="lalr"` and
  `maybe_placeholders=False`. If you extend the grammar, watch for
  shift/reduce conflicts; run `Parser(debug=True)` to surface Lark's
  diagnostic output while iterating.

## Where each piece is implemented

| Concern                   | File                                    |
| ------------------------- | --------------------------------------- |
| Grammar                   | `dsl/parser/grammar.lark`               |
| Parse tree → IR transform | `dsl/parser/_parser.py`                 |
| IR dataclasses            | `dsl/parser/_ir.py`                     |
| Public parser entry point | `Parser` class, `dsl/parser/_parser.py` |
