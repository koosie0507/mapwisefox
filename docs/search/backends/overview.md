# Backends overview

A `SearchBackend` (`backends/_base.py`) takes the `QueryObject` an adapter
produced and executes it: either printing it for a human to use manually, or
calling a live vendor API and persisting the results.

```python
class SearchBackend(metaclass=ABCMeta):
    def __init__(self, save_result=False, persistence_adapter=None): ...

    @abstractmethod
    def _perform_query(self, query_obj: QueryObject): ...

    def __call__(self, query_obj: QueryObject):
        results = self._perform_query(query_obj)
        self._save(results)  # no-op unless save_result and persistence_adapter are set
```

Implementing a new backend means overriding `_perform_query`, which returns
whatever `_save` (and its `PersistenceAdapter`) knows how to persist — in
practice, always a `pandas.DataFrame` for the API-backed vendors.

## Console vs. API backends

| Type    | Example                                                                                                          | Behavior                                                                                                                                   |
| ------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Console | `ConsoleBackend` (used directly by ACM and IEEE Xplore in the example config)                                    | Prints the query, regex hints, and filters to stdout for the user to paste into the vendor's own search UI — no HTTP call, no persistence. |
| API     | `ScienceDirectBackend`, `ScopusBackend`, `SpringerBackend`, `WebOfScienceBackend` (when `use_starter_api: true`) | Calls the vendor's HTTP API directly, paginating as needed, and saves a `DataFrame` via a `PersistenceAdapter`.                            |

`WebOfScienceBackend` is the one backend that can act as either, controlled
by its `use_starter_api` option — see [Web of Science](web-of-science.md).

## Concurrency model (driven by `__main__.py`)

- A `BackendSpec.is_console_backend` property (in `_config.py`) determines
  which category a configured backend falls into.
- All console backends run **first**, and **strictly sequentially** — so
  their interactive stdout output is never interleaved with logging from
  concurrent API calls.
- All remaining backends then run **concurrently**, inside a
  `ThreadPoolExecutor(max_workers=...)` (CLI option `--max-workers`, default
  `3`).
- A failure in one backend is caught, logged, and does not stop the others;
  with `--debug`, failure tracebacks are printed after the run completes.

## Output schema

Every API backend that returns a `DataFrame` aims for a roughly consistent
column set, though **coverage isn't identical across vendors** — check each
backend's page. The common columns are: `title`, `abstract`, `keywords`,
`authors`, `source`, `doi`, `url`, `year`. Web of Science's starter-API path
is the outlier — see [Web of Science](web-of-science.md).

## Persistence

Backends don't write files directly; they hand a `DataFrame` (or nothing) to
a `PersistenceAdapter` (`persistence/`), currently `PandasCsvAdapter` (CSV) or
`PickleAdapter` (pickle). See
[Configuration → Persistence](../configuration/persistence.md) for how
`csv_path`/`persistence_adapter` options resolve to actual file paths.
