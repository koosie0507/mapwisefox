# Usage

The `search` command runs a single DSL query against multiple academic search backends, translating your query into each vendor's native syntax automatically.

## Config file structure

Every `search` run requires a YAML configuration file with two parts:

1. **`query`** (or **`query_file`**): the DSL search text (see [DSL](../dsl/overview.md) for the query language).
2. **`backends`**: a list of backend specifications, each pairing an **adapter** (DSL → vendor query translator) with a **backend** (console printer or live API caller).

```yaml
query: |
  "machine learning" in title

backends:
  - name: ACM
    adapter: AcmDSLAdapter
    backend: ConsoleBackend
```

If you prefer to keep the query in a separate file, use `query_file: path/to/query.dsl` instead of `query:` — relative paths are resolved relative to the config file itself.

## Safe example: ConsoleBackend (no API keys required)

This example runs the query through all six supported adapters using only `ConsoleBackend`, which prints the translated query to your terminal without making any network calls — perfect for learning the CLI, testing query syntax, or verifying adapter output before setting up live backends.

```yaml
--8<-- "search/config.basic.yaml"
```

Run it with:

```bash
uv run search --config search/config.basic.yaml
```

or via the environment variable:

```bash
MWF_SEARCH_CONFIG=search/config.basic.yaml uv run search
```

### What happens

The CLI will:

1. Parse the DSL query once into an intermediate representation (IR).
2. Run each backend entry sequentially (since they're all console backends):
   - Instantiate the specified adapter (e.g., `AcmDSLAdapter`)
   - Translate the IR into a `QueryObject` (query string + filters + regex patterns)
   - Print the results to stdout via `ConsoleBackend`

You'll see output like this for each adapter:

```
The console adapter is used in the absence of an automated way to fetch results
Copy/paste the query below
----------------------------------------------------------------------------------------
(Title:(("entity resolution" OR "entity alignment" OR ...) AND ("system" OR ...)))
----------------------------------------------------------------------------------------
use these filters in the UI:

Article Type=['Research Article']
E-Publication Date=['(01/01/2010 TO 12/31/2025)']

----------------------------------------------------------------------------------------
```

Each adapter produces vendor-specific query syntax (ACM uses `Title:`, Scopus uses `TITLE-ABS`, etc.), and some adapters produce **filters** (ACM, IEEE Xplore) or **regex patterns** (Springer) for fields that can't be queried server-side.

## Real backend example: Springer

To run a live API backend, replace `ConsoleBackend` with a backend class that makes actual HTTP requests.
Here's a minimal Springer example:

```yaml
query: |
  "machine learning" in keywords and "arrhythmia" in title

backends:
  - name: Springer
    adapter: SpringerDSLAdapter
    backend:
      type: SpringerBackend
      options:
        api_key: ${MWF_SEARCH_SPRINGER_API_KEY}
        csv_path: springer.csv
        # the 'machine learning' query might yield too many results to handle
        fetch_all: false 
```

Run it the same way:

```bash
MWF_SEARCH_SPRINGER_API_KEY=your-key-here uv run search --config myconfig.yaml
```

or load the key from a `.env` file (see [Installation](installation.md#api-keys)).

There's a few things that are different compared to the first, basic example:

- **`backend.type` + `backend.options`**: Instead of a bare string like `ConsoleBackend`, live backends need constructor options — at minimum an `api_key`, and usually a `csv_path` to specify where results are written (see [Configuration](../configuration/config-file.md)).
- **Execution order**: Live API backends (anything other than `ConsoleBackend` or `WebOfScienceBackend` with `use_starter_api: false`) run **concurrently** after console backends finish, bounded by `--max-workers` (default 3). See [CLI Reference](cli-reference.md#execution-model) for the full diagram.
- **Output**: Results are written to CSV files under `<data-dir>/<results-dir-name>/<YYYYMMDD of most recent Monday>/`.

For other backends (ScienceDirect, Scopus, Web of Science, ACM, IEEE Xplore), see the [Backends](../backends/overview.md) section for endpoint details, constructor options, and output schemas.

If the query is successful, you'll see the search results in the following directory:

```
<data-dir>/<results-dir-name>/<YYYYMMDD of the most recent Monday>/
```

- `--data-dir` defaults to `./data` (env: `DATA_DIR`)
- `--results-dir-name` defaults to `search-results`
- The weekly-Monday bucket means re-running `search` multiple times in the same week overwrites the same output directory — handy for iterating on a query without accumulating stale CSVs. Pass `--disable-weekly-bucket` to turn this off and write straight into `<data-dir>/<results-dir-name>/`.

Relative `csv_path`s or `persistence_adapter` paths in a backend's options are resolved **relative to the results directory**.

Console backends (`ConsoleBackend` and `WebOfScienceBackend` with `use_starter_api: false`) only print to ``stdout`` without writing any CSV files.

## Iterate on the query

Edit the `query:` block (or your `query_file:`), rerun `search`, and repeat. The DSL supports:

- Boolean operators (`&`, `|`, `~`)
- Field scopes (`in title,abstract,keywords`)
- Wildcards (`tool*`)
- Phrase search (`"entity resolution"`)
- Date ranges (`published between "2010" and "2025"`)
- Proximity search (`near[5]("machine", "learning")`)
- Output targets (`[->filter: ...]`, `[->query: ...]`)

See the [DSL](../dsl/overview.md) section for the full syntax reference.
