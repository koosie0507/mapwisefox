# Installation

The assistant is part of the MapwiseFox uv workspace. From the repository
root, install or synchronize all workspace packages:

```bash
uv sync --all-packages
```

Verify the command is available:

```bash
uv run assistant --help
```

## Providers

The CLI supports these providers:

| Provider | Configuration |
|---|---|
| Ollama | `--ollama-host`, `--ollama-port`; no API key required |
| OpenAI | `MWF_ASSISTANT_API_KEY` or `--api-key` |
| Anthropic | `MWF_ASSISTANT_API_KEY` or `--api-key` |
| Google | `MWF_ASSISTANT_API_KEY` or `--api-key` |
| AWS Bedrock | AWS bearer token through `MWF_ASSISTANT_API_KEY` or `--api-key` |

The provider and model are global options and must appear before the
subcommand:

```bash
uv run assistant --provider openai --model gpt_5_mini study-selection --help
```

Never put API keys in a committed configuration file.
