# Operators

## Boolean operators

| Operator | Meaning | IR node                     |
| -------- | ------- | --------------------------- |
| `&`      | AND     | `BinaryExpr(op=BoolOp.AND)` |
| `\|`     | OR      | `BinaryExpr(op=BoolOp.OR)`  |
| `!`      | NOT     | `UnaryExpr(op=BoolOp.NOT)`  |

`&` and `|` bind expressions together. The `!` operator only negates the single
value immediately following it (e.g., `!"a" in title`). To negate a group,
restructure the query or apply negation to the values inside the group.

## Field scoping

| Syntax                          | Meaning                                          |
| ------------------------------- | ------------------------------------------------ |
| `<expr> in field`               | Scope `<expr>` to one field                      |
| `<expr> in field1, field2, ...` | Scope `<expr>` to multiple fields (OR semantics) |

## Match operators

These wrap a single value expression: `match_op "(" value_expr ")"`.

### `approx(...)`

```
approx("data science") in title
```

Parses to `MatchExpr(op=MatchOp(kind="approx"), child=ValueExpr(...))`.
Intended to signal "fuzzy/approximate match" to backends that support it.

### `nearest[n](...)`

```
nearest[5]("a") in abstract
```

Parses to `MatchExpr(op=MatchOp(kind="nearest", arg=5), ...)`. Intended for
proximity search (e.g. "these terms within N words of each other").

### `match[type](...)`

```
match[strict]("a")
match[loose]("a")
match[regex]("a\s+b")
```

`type` is one of `strict`, `loose`, `regex` (`MatchType` enum). The `strict`
and `loose` specifiers are converted only if they're supported in the backend
as part of the query (see [Output Specification](./output-spec.md)).

On the other hand, the `regex` specifier always feeds the operand into the
[regex-handling](../architecture/regex-handling.md) machinery in the base
adapter, letting you express client-side post-filtering for fields a vendor
backend can't search directly (see the [Springer backend](../backends/springer.md),
which can't query `title`/`abstract` server-side).

!!! note
    `approx`, `nearest`, `match[strict]` and `match[loose]` are parsed in the IR, but
    their default transformation is a pure pass-through, meaning the result is simply
    the wrapped value expression without adding specific vendor fuzzy/proximity logic. 
    Only `match[regex]` has special default handling: it's treated as a client-side
    regex applied after retrieval (see [regex handling](../architecture/regex-handling.md)),
    not as part of the query term itself. When implementing a vendor backend that supports
    these features natively, override the `emit_approx`, `emit_nearest`, or `emit_match`
    in that adapter.

## Date operators

See [Dates](dates.md).

## Output-target operator

See [Output spec](output-spec.md) for `[->query: ...]` / `[->filter: ...]`.
