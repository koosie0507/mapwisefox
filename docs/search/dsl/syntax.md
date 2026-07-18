# Syntax

## Values

The atomic building block is a quoted string:

```
"machine learning"
```

This is a `ValueExpr` in the IR. On its own it has no field scope — some
adapters (e.g. Scopus, WoS) fall back to a default field context when none is
given, others (e.g. ACM) simply drop unscoped values. In practice you'll
almost always scope it with `in`:

```
"machine learning" in title
```

## Field scoping (`in`)

`in` attaches one or more field names to the expression immediately to its
left — a value, a match expression, a date expression, a group, or a whole
binary expression:

```
"machine learning" in title
"deep learning" in title, abstract, keywords
```

Multiple fields mean "match in any of these," and adapters render this as an
`OR` across per-field clauses, or a single combined field alias where the
vendor supports one (e.g. Scopus collapses `title, abstract` into its native
`TITLE-ABS` field — see
[Architecture → Field mapping](../architecture/field-mapping.md)).

Recognized field names (the union any adapter might understand — a given
adapter only supports the subset relevant to that vendor):

`title`, `abstract`, `keywords`, `author`, `affiliation`, `evidence_type`,
`language`, `subject`, `published`.

## Boolean composition

```
"a" in title & "b" in abstract      # AND
"a" in title | "b" in title         # OR
!"a" in title                       # NOT
```

- `&` and `|` combine two expressions (`BinaryExpr`, `BoolOp.AND`/`BoolOp.OR`).
- `!` negates a single value expression (`UnaryExpr`, `BoolOp.NOT`) and can
  itself carry an `in` clause: `!"a" in title, abstract`.

## Grouping

Parentheses group sub-expressions and can themselves carry an `in` clause
that applies to the whole group:

```
("a" | "b") in title
```

This parses to a `GroupExpr` wrapping a `BinaryExpr`, with `fields=["title"]`
on the group itself (not on the inner values) — the adapter is responsible
for pushing that field scope down when it renders the group.

Nesting is unrestricted:

```
("a" in title & "b" in abstract) | "c" in title
```

## Dates

```
published between "2010" and "2025"
published after "2015"
published before "2020"
```

See [Dates](dates.md) for the full semantics, including how year-only bounds
get expanded to full-year ranges.

## Match operators

```
approx("a") in title
nearest[5]("a") in abstract
match[regex]("a\s+b") in title
```

See [Operators](operators.md) for their meaning.

!!! note
    All operators are parsed into the IR, but only adapters for supported
    backends convert them to native syntax. By default, the native
    representation of inner nodes bubbles up unchanged.

## Output targeting

```
[->filter: "english" in language]
[->query: "AI" in title]
```

Wraps a sub-expression and tags it as intended for a backend's filter
mechanism vs. its free-text query — see [Output spec](output-spec.md).

## What's *not* valid

- An `attr_clause` (`in ...`) can only attach to the expression immediately
  preceding it — you can't retroactively scope something several tokens back.
  In order to achieve those semantics, use groups.
- Unterminated strings and unknown match operators (e.g. `frobnicate(...)`)
  are hard parse errors (`lark.exceptions.UnexpectedInput`), not silently
  ignored.
