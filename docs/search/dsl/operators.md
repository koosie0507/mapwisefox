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
    `approx`, `match[strict]` and `match[loose]` are parsed in the IR, but
    their default transformation is a pure pass-through, meaning the result is simply
    the wrapped value expression without adding specific vendor fuzzy/proximity logic. 
    Only `match[regex]` has special default handling: it's treated as a client-side
    regex applied after retrieval (see [regex handling](../architecture/regex-handling.md)),
    not as part of the query term itself. When implementing a vendor backend that supports
    these features natively, override the `emit_approx` or `emit_match` in that adapter.

## Proximity operator

### `near[n](value1, value2)`

```
near[5]("machine", "learning") in title
```

Unlike `approx`/`match`, `near` is **not** a `match_op` wrapping a single value
— it's its own `NearExpr` IR node that always takes exactly **two** literal
string values plus an integer distance:

```
NearExpr(distance=5, left=ValueExpr(value="machine"), right=ValueExpr(value="learning"), fields=["title"])
```

This models real-world proximity search as implemented by vendors like Scopus
and Springer: "`value1` is at most `n` words from `value2`", in either order
— **not** a "k-nearest-neighbors" style search. `near` supports field scoping
(`in field1, field2, ...`) exactly like the other operators.

!!! note
    By default, `near[n](a, b)` degrades to a plain, always-parenthesized
    `AND` of both terms — i.e. `(a AND b)` — since most backends don't have a
    native proximity operator. Backends that do should override `emit_near`:

    - **Scopus** translates to its native `W/n` operator: `"a" W/n "b"`.
    - **Springer** and **Web of Science** translate to their native `NEAR/n`
      operator: `"a" NEAR/n "b"`.

    On fields that are regex-only for a given backend (e.g. `title`/`abstract`
    on Springer), `near(...)` instead degrades to a distance-aware,
    order-insensitive regex lookahead — see
    [regex handling](../architecture/regex-handling.md).

## Date operators

See [Dates](dates.md).

## Output-target operator

See [Output spec](output-spec.md) for `[->query: ...]` / `[->filter: ...]`.
