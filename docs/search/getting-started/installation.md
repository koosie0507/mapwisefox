# Installation

`search` is installed as part of the whole `mapwisefox` workspace — see
[Getting Started → Installation](../../getting-started/installation.md) for
cloning the repo and running `uv sync`. That single sync installs `search`
and its console entry point (`search`, defined in `search/pyproject.toml`
under `[project.scripts]`) along with every other workspace member.

## API keys

Every backend except ACM and IEEE Xplore (which are console-only — see
[Backends](../backends/overview.md)) needs an API key, supplied via
environment variables:

| Backend | Env var |
|---|---|
| ScienceDirect | `MWF_SEARCH_ELSEVIER_API_KEY` |
| Scopus | `MWF_SEARCH_ELSEVIER_API_KEY` |
| Springer | `MWF_SEARCH_SPRINGER_API_KEY` |
| Web of Science | `MWF_SEARCH_CLARIVATE_API_KEY` |

Add these to the repo-root `.env` described in
[Getting Started → Environment variables](../../getting-started/installation.md#environment-variables-and-env):

```dotenv
MWF_SEARCH_ELSEVIER_API_KEY=your-key-here
MWF_SEARCH_SPRINGER_API_KEY=your-key-here
MWF_SEARCH_CLARIVATE_API_KEY=your-key-here
```

Any config value in the YAML config file — not just backend options — is
passed through `os.path.expandvars`, so `${MY_ENV_VAR}` references anywhere in
the file (not only in `backend.options`) will be expanded against the process
environment (and therefore against `.env`, once loaded).

!!! warning
    Never commit real API keys. Use `${VAR}` placeholders in configs you check
    into source control, exactly like `config.example.yaml` does.
