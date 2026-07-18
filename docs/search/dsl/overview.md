# DSL overview

The search DSL is a small boolean query language, purpose-built so it can be
used in `mapwisefox.web` and be rich enough to express what systematic-review
searches actually need: phrase matching, wildcards, field scoping, date ranges,
and a way to say "use these clauses as query text on some backends, but as
post-search filters on others."

Grammar source: `search/src/mapwisefox/search/dsl/parser/grammar.lark`
(annotated in full at [Reference → Grammar](../reference/grammar.md)).

## The pipeline

1. **Parse** — `Parser` (Lark, LALR) turns DSL text into a Lark parse tree.
2. **Transform** — a `Transformer` + `lark.ast_utils.create_transformer`
   convert that parse tree into a typed intermediate representation (IR): a
   tree of dataclasses defined in `_ir.py` (see
   [Architecture → IR](../architecture/ir.md)).
3. **Adapt** — a `DSLAdapter` subclass (one per vendor) walks the IR and
   produces a `QueryObject`: a vendor-native query string, plus optional
   filters and/or regex patterns (see
   [Architecture → Adapters](../architecture/adapters.md)).
4. **Execute** — a `SearchBackend` takes that `QueryObject` and either prints
   it for manual use, or calls a live API and saves the results.

## A complete example

This is the running example used throughout these docs (it's also a fixture,
`ersa_query_text`, shared by the test suite):

```
(
  (
    ("entity resolution" | "entity alignment" | "record linkage" | "data deduplication" | "merge/purge" | "entity linking" | "entity matching")
      &
    ("system" | "tool*" | "framework" | "architect*" | "library")
  ) in title,abstract
) & (
  ("entity resolution" | "entity alignment" | "record linkage" | "data deduplication" | "merge/purge" | "entity linking" | "entity matching") in keywords
) & (
  [->filter: "english" in language & ("article" | "conference") in evidence_type & "computer science" in subject & published between "2010" and "2025"]
)
```

Read as: (title or abstract mentions an ER synonym AND a system/tool synonym)
AND (keywords mention an ER synonym) AND (English, article-or-conference,
computer-science, published 2010–2025 — expressed as filters rather than
free-text query terms).

Continue to [Syntax](syntax.md) for a term-by-term breakdown, or
[Operators](operators.md) for the full operator reference.
