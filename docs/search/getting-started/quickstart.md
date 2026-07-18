# Quickstart

## 1. Write or copy a config file

`search/config.example.yaml` is a complete, runnable example. It has two
parts: a `query` (the DSL text) and a list of `backends` to run that query
against.

```yaml
--8<-- "search/config.example.yaml"
```

## 2. Run it

```bash
uv run search --config search/config.example.yaml
```

or, equivalently, point the `MWF_SEARCH_CONFIG` env var at it instead of
passing `--config`:

```bash
MWF_SEARCH_CONFIG=search/config.example.yaml uv run search
```

## 3. What happens

1. The `query` DSL text is parsed once into an IR (`Query`).
2. For each entry under `backends`, the configured `adapter` translates that
   IR into a vendor-native `QueryObject`, and the configured `backend`
   executes it.
3. **Console backends** (ACM, IEEE Xplore — anything using `ConsoleBackend`,
   or Web of Science with `use_starter_api: false`) run first and
   sequentially, printing the translated query string (and any filters) to
   your terminal for you to paste into that vendor's search UI by hand.
4. Every other backend then runs **concurrently** (bounded by `--max-workers`,
   default 3) against its live API, and writes results to CSV.

## 4. Where results go

Results land under:

```
<data-dir>/<results-dir-name>/<YYYYMMDD of the most recent Monday>/
```

- `--data-dir` defaults to `./data` (env: `DATA_DIR`).
- `--results-dir-name` defaults to `search-results`.
- The weekly-Monday bucket means re-running `search` multiple times in the
  same week overwrites the same output directory — handy for iterating on a
  query without accumulating stale CSVs. Pass `--disable-weekly-bucket` to
  turn this off and write straight into `<data-dir>/<results-dir-name>/`.

Any relative `csv_path` or `persistence_adapter` path in a backend's options
is resolved **relative to that dated results directory** — see
[Configuration](../configuration/config-file.md).

## 5. Iterate on the query

Edit the `query` block (or point at a separate file with `query_file:`
instead — paths there are resolved relative to the config file itself), rerun
`search`, and repeat. See [DSL](../dsl/overview.md) for the query language
itself.
