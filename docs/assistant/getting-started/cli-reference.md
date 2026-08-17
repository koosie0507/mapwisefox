# CLI Reference

The `assistant` is a group of commands. You can access a description by running:

```bash
uv run assistant --help
```

## Shared Options

If used, the following options must be provided before the subcommand.

| Option | Default | Description |
|---|---|---|
| `--model`, `-m` | `gpt-oss:20b` | Model choice exposed by the selected provider. |
| `--provider`, `-p` | `ollama` | LLM provider to use. One of `ollama`, `openai`, `anthropic`, `google`, `aws-bedrock`. |
| `--ollama-endpoint` | `http://localhost:11434` | Address where Ollama is listening. Used only with `-p ollama`. |
| `--api-key` | — | Provider API key; also available through `MWF_ASSISTANT_API_KEY`. Required for `openai` and `anthropic`. |

## `study-selection`

```bash
uv run assistant study-selection --help
```

| Argument or option | Default | Description |
|---|---|---|
| `SEARCH_RESULTS` | required | Input `.xlsx`, `.csv`, or `.bib` study records. |
| `--config-file`, `-c` | required | Selection JSON config; also `MWF_ASSISTANT_SELECTION_CONFIG`. |
| `--limit` | all rows | Maximum number of records to process. |
| `--ignore-attributes`, `-i` | `cluster_id`, `include`, `exclude_reason` | Columns omitted from the per-record prompt. Repeat to add more. |
| `--sheet-name`, `-s` | first worksheet | Name of the worksheet containing the input records. |

The output is an `.xlsx` file beside the input with the model name appended
(`{input-stem}-{model}.xlsx`, with `:` in the model name replaced by `_`).

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
| `--layout-model`, `-l` | `lp://PubLayNet/tf_efficientdet_d0/config` | LayoutParser model used by the `custom` reader. |
| `--insecure-skip-tls-verify` | disabled | Disable TLS verification for HTTP PDF downloads. |
| `--download-dir`, `-D` | `./downloads` | Directory where downloaded primary-study PDFs are stored. |

The output workbook contains one criterion score column per QA criterion and
an `evaluation` column. It is written beside the input as
`{file-stem}-{model}{file-suffix}`.

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
