# Config file

Validated by `mapwisefox.search._config.SearchConfig` (Pydantic).

## Top-level shape

```yaml
query: |
  ...DSL text...
# or: query_file: path/to/query.dsl

backends:
  - name: <unique label>
    adapter: <DSLAdapter class name>
    backend: <BackendRef>
    adapter_options: {} # optional, kwargs for the adapter constructor
```

- Exactly one of `query` / `query_file` must be set — `SearchConfig`'s
  model validator rejects configs with both or neither.
- `query_file` paths are resolved relative to the config file's own
  directory (not the current working directory).
- `backends` must have at least one entry, and every `name` must be unique
  (both are enforced validators on `SearchConfig`/`BackendSpec`).

## `backend:` shorthand vs. full form

```yaml
backend: ConsoleBackend # shorthand — no options needed

backend: # full form
  type: ScopusBackend
  options:
    api_key: ${MWF_SEARCH_ELSEVIER_API_KEY}
    csv_path: scopus.csv
```

`BackendSpec._normalize_backend` accepts a bare string as shorthand for
`{type: <string>}`. Both `adapter` and `backend.type` are validated against
the classes actually exported from `mapwisefox.search.dsl.adapters.__all__`
and `mapwisefox.search.backends.__all__` respectively (minus the abstract
base classes) — an unknown name fails validation immediately with the list
of valid names in the error message.

## Environment variable expansion

Every string value anywhere in the config — not just inside `backend.options`
— is passed through `os.path.expandvars` before use, so `${VAR}` (or `$VAR`)
references are resolved against the process environment. A `.env` file at
the repo root is loaded automatically at startup (via `dotenv.load_dotenv()`
in `__main__.py`), so this is the natural place to keep API keys out of
version control.

## Path resolution for backend options

Two specific option keys get special treatment, resolved relative to the
run's results directory (`<data-dir>/<results-dir-name>/`, or
`<data-dir>/<results-dir-name>/<Monday's date>` with `--enable-weekly-bucket`):

- `csv_path`: wrapped as-is, resolved relative to that directory.
- `persistence_adapter`: if given as a string/path, it's wrapped in a
  `PandasCsvAdapter` pointed at that resolved path (see
  [Persistence](persistence.md)).

This happens in `_resolve_backend_options` in `__main__.py`, _after_ env var
expansion — so `csv_path: ${OUT_DIR}/scopus.csv` would expand the env var
first, then still be joined onto the results directory (this
combination is unusual and likely not what you want — prefer a bare relative
filename for `csv_path` in normal use).

## `BackendSpec.is_console_backend`

Determines whether a backend runs in the sequential "console" phase or the
concurrent "API" phase (see [Backends overview](../backends/overview.md)):
true when `backend.type` is a `ConsoleBackend` subclass, **or** it's
`WebOfScienceBackend` with `use_starter_api` falsy in its options.
