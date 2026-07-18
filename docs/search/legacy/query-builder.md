# Query builder (deprecated)

!!! danger "Deprecated — use the DSL instead"
    `mapwisefox.search.query.builder` is the original, code-first way of
    constructing search queries. It predates the [DSL](../dsl/overview.md)
    and is being phased out. **New queries should be written in the DSL.**

This Python API is useful for building searches programmatically, but it fails
on two important fronts:

- it can't be embedded in a textarea on a web page - every query change requires
  editing;
- the resulting query builder can't easily be shared.

## Example

```python
from mapwisefox.search.query.builder import QueryBuilder, TitleAbsExpr, EvidenceTypes, SubjectAreas

query = QueryBuilder().year_range(2010, 2025)
query.groups(
    query.and_group(
        query.or_group(*map(TitleAbsExpr, er_terms)),
        query.or_group(*map(TitleAbsExpr, qualifiers)),
    )
).doc_types(
    EvidenceTypes.ARTICLE, EvidenceTypes.CONFERENCE
).subject_areas(
    SubjectAreas.COMPUTER_SCIENCE
).languages(
    "english"
).keywords(
    *er_terms
)

query.build(ScopusAdapter)
```

`tests/conftest.py`'s `ersa_query_builder` fixture builds exactly this, as
the direct legacy equivalent of the DSL's `ersa_query_text` fixture used
throughout the rest of these docs — comparing the two side by side is the
fastest way to see what the DSL saves you from writing.

## Equivalence with DSL

Generally speaking, the search DSL is far more expressive and feature complete than
the query builder at this point.

| Query builder                                                 | DSL equivalent                                 |
| ------------------------------------------------------------- | ---------------------------------------------- |
| `TitleExpr("x")`                                              | `"x" in title`                                 |
| `AbstractExpr("x")`                                           | `"x" in abstract`                              |
| `TitleAbsExpr("x")`                                           | `"x" in title, abstract`                       |
| `TitleAbsKeysExpr("x")`                                       | `"x" in title, abstract, keywords`             |
| `AuthorKeysExpr("x")`                                         | `"x" in keywords`                              |
| `LanguageExpr("english")`                                     | `"english" in language`                        |
| `SubjectAreaExpr(SubjectAreas.COMPUTER_SCIENCE)`              | `"computer science" in subject`                |
| `EvidenceTypeExpr(EvidenceTypes.ARTICLE)`                     | `"article" in evidence_type`                   |
| `YearRangeExpr(2010, 2025)`                                   | `published between "2010" and "2025"`          |
| `query.and_group(a, b)`                                       | `a & b`                                        |
| `query.or_group(a, b)`                                        | `a \| b`                                       |
| `.doc_types(EvidenceTypes.ARTICLE, EvidenceTypes.CONFERENCE)` | `("article" \| "conference") in evidence_type` |
| `query.build(SomeAdapter)`                                    | `AdapterClass().adapt(Parser()(dsl_text))`     |

!!! warning "Enum value mismatch"
The legacy `EvidenceTypes` enum value literals are different than the
DSL's: `EvidenceTypes.ARTICLE = "journal"` (legacy) vs. the DSL's literal
`"article"`. The translation of query-builder call sites to their equivalent
DSL is semantic. Copy-paste does not help here.

## Call to Action

The `mawisefox.search.query.builder` package is on its way out. It will be
removed before the `1.0` release of the `mapwisefox.search` package. Using
it is strongly discouraged. Existing code must be ported to the equivalent
DSL.
