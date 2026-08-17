# Persistence

`mapwisefox.search.persistence` defines a small `Protocol`,
`PersistenceAdapter`, with a single method: `save(self, obj)`. Backends never
write files directly — they hand their result (typically a
`pandas.DataFrame`) to whatever `PersistenceAdapter` they were configured
with.

## Built-in adapters

| Adapter | Behavior |
|---|---|
| `PandasCsvAdapter(csv_file)` | `save(obj)` requires `obj` to be a `pandas.DataFrame`; writes it via `DataFrame.to_csv(csv_file, index=False)`. Used by every live-API backend today. |
| `PickleAdapter(csv_file)` | `save(obj)` pickles `obj` (any picklable object, not just a `DataFrame`) via `pickle.dump(..., pickle.HIGHEST_PROTOCOL)`. Not currently wired up to any backend by default — available for custom use. |

## How backends get one

Most API backends build their own `PandasCsvAdapter` internally from a
`csv_path` constructor option (see each backend's page in
[Backends](../backends/overview.md)) — `csv_path` is resolved relative to
the results directory by `__main__.py` before being passed to the
backend's constructor.

`WebOfScienceBackend` is the exception: it takes a `persistence_adapter`
option directly (rather than a `csv_path`), because the config schema
supports pointing `persistence_adapter` at a plain filename and having
`__main__.py` wrap it in a `PandasCsvAdapter` automatically (see
[Config file → path resolution](config-file.md)).

## Saving is opt-in

`SearchBackend._save()` only calls `persistence_adapter.save(...)` when both
`save_result` is truthy *and* `persistence_adapter` is not `None` — so a
backend configured without a `csv_path`/`persistence_adapter` silently skips
persistence rather than erroring. This is deliberate for
`WebOfScienceBackend` in non-starter-API (console) mode, where saving is
forced off regardless of configuration.
