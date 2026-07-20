# Field mapping

Each adapter declares its own `_FIELD_MAP` (DSL field name → vendor field
name) and, where the vendor uses different literal values, a `_VALUE_MAP`
(e.g. DSL `"article"` → ACM's `"Research Article"`). A field with no entry in
`_FIELD_MAP` is simply unsupported by that adapter — clauses using it are
dropped rather than erroring.

| DSL field       | ACM                                               | ScienceDirect                        | Scopus                                                                         | Springer                                         | Web of Science | IEEE Xplore                                              |
| --------------- | ------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------ | -------------- | -------------------------------------------------------- |
| `title`         | `Title`                                           | `TITLE`                              | `TITLE` (combines with `abstract`/`keywords` into `TITLE-ABS`/`TITLE-ABS-KEY`) | `title` — regex-only, not searchable server-side | `TI`           | `Document Title`                                         |
| `abstract`      | `Abstract`                                        | `ABSTRACT`                           | `ABS` (see combining above)                                                    | `abstract` — regex-only                          | `AB`           | `Abstract`                                               |
| `keywords`      | `Keyword`                                         | `KEYWORDS`                           | `AUTHKEY` (see combining above)                                                | `keyword`                                        | `AK`           | `Author Keywords`                                        |
| `author`        | unsupported                                       | `AUTHORS`                            | `AUTH`                                                                         | `name`                                           | unsupported    | `Authors`                                                |
| `affiliation`   | unsupported                                       | unsupported                          | `AFFIL`                                                                        | unsupported                                      | unsupported    | `Author Affiliations`                                    |
| `evidence_type` | `Article Type` (filter only)                      | `CONTENT-TYPE`                       | `DOCTYPE`                                                                      | `type`                                           | `DT`           | `content_type` (**always** a filter, output-spec or not) |
| `language`      | unsupported                                       | unsupported                          | `LANGUAGE`                                                                     | `language` (premium accounts only)               | `LA`           | unsupported                                              |
| `subject`       | unsupported                                       | unsupported                          | `SUBJAREA`                                                                     | `discipline` (premium accounts only)             | `WC`           | unsupported                                              |
| `published`     | `E-Publication Date` (filter, `MM/DD/YYYY` range) | `PUB-DATE` (`AFT`/`BEF`, `YYYYMMDD`) | `PUBYEAR` (`AFT`/`BEF`, widened ±1 year for year-only bounds)                  | `datefrom`/`dateto` filters                      | `DOP` (range)  | `start_year`/`end_year` query params                     |

## Value translations (`_VALUE_MAP`) worth knowing

| DSL value            | Field           | ACM                | ScienceDirect                         | Scopus                                | Springer                     | WoS                | Xplore        |
| -------------------- | --------------- | ------------------ | ------------------------------------- | ------------------------------------- | ---------------------------- | ------------------ | ------------- |
| `"article"`          | `evidence_type` | `Research Article` | `JL`                                  | `ar`                                  | `Journal`                    | `Article`          | `Journals`    |
| `"conference"`       | `evidence_type` | `Research Article` | _unmapped — passed through literally_ | `cp`                                  | `Journal`                    | _unmapped_         | `Conferences` |
| `"computer science"` | `subject`       | n/a (unsupported)  | n/a                                   | `COMP`                                | `Computer Science` (premium) | `Computer Science` | n/a           |
| `"english"`          | `language`      | n/a                | n/a                                   | _unmapped — passed through literally_ | `English` (premium)          | `English`          | n/a           |

Two gaps worth flagging explicitly:

- **ScienceDirect's `evidence_type` map has no `"conference"` entry** — a
  `"conference" in evidence_type` clause will pass the literal string
  `"conference"` through rather than a ScienceDirect-native value.
- **Scopus has no `language` value map** — `"english" in language` becomes
  `LANGUAGE("english")` verbatim, which happens to work for Scopus (it
  accepts free-text language names) but is worth confirming if you introduce
  a differently-cased or non-English value.

## Combined-field collapsing (Scopus only)

`ScopusDSLAdapter._COMBINED` collapses a multi-field `in` clause into a single
Scopus alias when the field set exactly matches a known combination:

```python
_COMBINED = {
    frozenset({"title", "abstract"}): "TITLE-ABS",
    frozenset({"title", "abstract", "keywords"}): "TITLE-ABS-KEY",
}
```

So `"x" in title, abstract` becomes `TITLE-ABS("x")` rather than
`TITLE("x") OR ABS("x")` — see `test_scopus.py::test_sanity_check`.
