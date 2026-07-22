# CLI Reference

The `assistant` is a group of commands. You can access a description by running:

```bash
uv run assistant --help
```

## Shared Options

If used, the following options must be provided before the subcommand.

| Option | Default | Description |
|---|---|---|
| `--model`, `-m` | `gpt_oss` | Model choice exposed by the selected provider. |
| `--provider`, `-p` | `ollama` | LLM provider to use. |
| `--ollama-host` | `localhost` | Ollama host. |
| `--ollama-port` | `11434` | Ollama port. |
| `--api-key` | — | Provider API key; also available through `MWF_ASSISTANT_API_KEY`. |

## `study-selection`

```bash
uv run assistant study-selection --help
```

| Argument or option | Default | Description |
|---|---|---|
| `SEARCH_RESULTS` | required | Input `.xlsx`, `.csv`, or `.bib` study records. |
| `--config-file`, `-c` | required | Selection JSON config; also `MWF_ASSISTANT_SELECTION_CONFIG`. |
| `--limit` | all rows | Maximum number of records to process. |
| `--ignore-attributes`, `-i` | `cluster_id`, `include`, `exclude_reason` | Columns omitted from the per-record prompt. |

The output is an `.xlsx` file beside the input with the model name appended.

## `study-qa`

```bash
uv run assistant study-qa --help
```

| Argument or option | Default | Description |
|---|---|---|
| `FILE` | required | Input workbook containing study PDF URLs or `file://` paths. |
| `--config`, `-c` | required | QA JSON config; also `MWF_ASSISTANT_QA_CONFIG`. |
| `--url-column`, `-u` | `url` | PDF URL/path column. |
| `--index-column` | — | Existing column to use as the row identifier. |
| `--reader-type`, `-e` | `custom` | `custom` or `docling` PDF reader. |
| `--layout-model`, `-l` | LayoutParser default | Layout model used by the custom reader. |
| `--insecure-skip-tls-verify` | disabled | Disable TLS verification for HTTP PDF downloads. |

The output workbook contains one criterion score column per QA criterion and
an `evaluation` column.

## `validate-config`

```bash
uv run assistant validate-config --help
```

| Option | Description |
|---|---|
| `--kind`, `-k` | `study-selection` or `study-qa`. |
| `--config-file`, `-c` | JSON file to validate. |

Validation uses the same data models as the processing commands and does not
contact an LLM provider.
