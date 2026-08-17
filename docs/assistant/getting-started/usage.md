# Usage

The assistant is intended to continue the workflow described in the existing
[Search usage example](../../search/getting-started/usage.md) and
[Deduplication usage example](../../deduplication/getting-started/usage.md).
Those commands produce the workbook that becomes the input to
`study-selection`.

## Study Selection

`study-selection` expects a spreadsheet containing at least a title, abstract,
and any metadata you want the LLM to consider. The example configuration keeps
the screening rules deliberately short and limited to information that can be
seen in the title, abstract, year, language, or publication type:

```json
--8<-- "assistant/examples/study-selection-config.json"
```

Run it against the deduplicated workbook:

```bash
uv run assistant \
  --provider ollama \
  --model gpt-oss:20b \
  study-selection data/output/<deduplicated-workbook>.xlsx \
  --config-file assistant/examples/study-selection-config.json
```

For a hosted provider, replace the global provider/model options and configure
`MWF_ASSISTANT_API_KEY` as described in [Installation](installation.md).

The output is written beside the input workbook with the model name appended.
It adds or updates:

| Column | Meaning |
|---|---|
| `include` | The LLM's `include` or `exclude` decision |
| `exclude_reason` | The justification for an excluded record |

Reviewers should inspect these decisions before continuing. Select the rows
whose `include` value is `include` and save them as the input workbook for
`study-qa`.

## Study QA

`study-qa` reads a spreadsheet containing a URL or `file://` path to each
primary-study PDF. The example configuration contains three representative
criteria: clear objectives, appropriate research design, and relevance to
software architecture.

```json
--8<-- "assistant/examples/study-qa-config.json"
```

Run quality assessment on the reviewed selection:

```bash
uv run assistant \
  --provider ollama \
  --model gpt-oss:20b \
  study-qa data/output/<selected-workbook>.xlsx \
  --config assistant/examples/study-qa-config.json
```

Use `--reader-type docling` to select the Docling reader, or leave the default
`custom` reader in place. The `--url-column` option changes the source column
when URLs are not stored in `url`.

The output contains one score column per criterion and an `evaluation` column
containing the grouped explanations. If the LLM cannot produce a usable score
after the configured attempts, the score remains empty rather than being
guessed.

By default, PDF downloads verify TLS certificates. Use
`--insecure-skip-tls-verify` only when a source has a known certificate problem
and the risk is understood.

## Validate Configuration

Validate either configuration without contacting an LLM provider:

```bash
uv run assistant validate-config \
  --kind study-selection \
  --config-file assistant/examples/study-selection-config.json

uv run assistant validate-config \
  --kind study-qa \
  --config-file assistant/examples/study-qa-config.json
```

The corresponding JSON Schemas are available in
`common-config/schemas/` for editor and external validation support.
