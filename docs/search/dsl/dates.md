# Dates

```
<field> between "<date>" and "<date>"
<field> after "<date>"
<field> before "<date>"
```

Dates are free-form strings at the grammar level (no format validation is
enforced in the parser itself). Parsing happens at the adapter level, typically
by using the [`arrow`](https://arrow.readthedocs.io/) package.

## Year-only bounds get expanded

If you write `published between "2010" and "2025"`, most adapters treat a
bound that equals `arrow.get(...).floor(frame="year")` as "just a year" and
expand it to cover the full year:

- The low bound floors to `YYYY-01-01`.
- The high bound ceils to `YYYY-12-31` (end of year).

This choice was made to accommodate a desire to search for works published
on "any date from the start of 2010 through the end of 2025," not literally
midnight Jan 1 2010 through midnight Jan 1 2025 (which would silently exclude
all of 2025).

## Per-vendor quirks worth knowing

| Vendor         | Notes                                                                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ACM            | `MM/DD/YYYY` bounds, inclusive range syntax `(lo TO hi)`                                                                                                                    |
| ScienceDirect  | `YYYYMMDD`, rendered as `FIELD AFT 'lo' AND FIELD BEF 'hi'`                                                                                                                 |
| Scopus         | Strict `>`/`<` semantics, so year-only bounds are widened by **one extra year** on each side (e.g. 2010–2025 becomes AFT 2009 / BEF 2026) to avoid excluding boundary years |
| Springer       | `datefrom:"..."` / `dateto:"..."` filter keys, ISO dates                                                                                                                    |
| Web of Science | `DOP=(lo/hi)`, `after` uses `lo/<today>`, `before` uses `1950-01-01/hi` as an open-ended floor                                                                              |
| IEEE Xplore    | There's no query level syntax. Instead only the date _year_ is taken into account and mapped to the `start_year`/`end_year` query params directly                           |

Because of these differences, don't assume a date range means exactly the
same thing byte-for-byte across backends — the DSL captures the _intent_
("published in this range"), and each adapter is responsible for the closest
faithful translation into that vendor's semantics.
