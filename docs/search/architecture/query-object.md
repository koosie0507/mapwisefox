# QueryObject

```python
class QueryObject(BaseModel):
    query: str = ""
    regex: dict[str, str] = Field(default_factory=dict)
    filters: dict[str, list[str]] = Field(default_factory=dict)
```

(`mapwisefox.search.query.QueryObject`, a Pydantic model.)

`QueryObject` defines the contract between adapters and backends. Every
`DSLAdapter.adapt(...)` call ultimately produces a `QueryObject` instance which
is consumed by a `SearchBackend.__call__`.

| Field     | Meaning                                                                                                                                                                                                                          |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`   | The vendor-native free-text query string, ready to send (or paste into a UI).                                                                                                                                                    |
| `filters` | A mapping containing a list of clauses (presented in vendor-native format) per field (empty string (`""`) when no field qualifier applies). This allows the backend to handle filter clauses in any way that is fit for purpose. |
| `regex`   | A mapping containing a regex pattern to apply on the client per field (see [Regex handling](regex-handling.md)). The empty string key (`""`) is used when no field qualifier applies.                                            |

## Building the `QueryObject` internally

The vast majority of `DSLAdapter.emit_*()` methods gradually build up a
`QueryObject` which expresses the DSL query. `DSLAdapter.emit_query()` is
the final assembly point — nearly every concrete adapter overrides it to
control the final `.query`, `.filters` and `.regex` that will be the input
of the `SearchBackend` implementation.

## Consumption by backends

- **Console backends** (`ConsoleBackend`) print `.query`, and if present,
  `.regex` and `.filters`, for a human to copy into a vendor's search UI.
- **API backends** send `.query` as the vendor's query parameter. Each
  backend chooses how to use `.filters` and `.regex` -- there aren't any
  default behaviours baked into the `SearchBackend` base class (yet).
