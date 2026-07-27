---
title: Installation
description: Set up MapwiseFox locally or run its tools from the published Docker image.
tags:
- installation
- workspace
---

# Installation

If you want to contribute to Mapwisefox, you should know that it is a
[uv](https://docs.astral.sh/uv/) workspace: one repo, one lockfile, several
independently-versioned Python packages sharing a single virtual environment,
plus a standalone React/TypeScript frontend.

## Docker

If you just want to _run_ the suite rather than develop against it, use the
published Docker image. It bundles every CLI in the suite, the API backend,
and the production web UI.

### Run the web app

```bash
docker run --rm -p 8000:8000 ghcr.io/koosie0507/mapwisefox:latest
```

Then open <http://localhost:8000>. Images are published to GHCR on
every `vX.Y.Z` tag. Both the tagged version and the `latest` tag
are updated in the container registry.

!!! note
    Dev/debug mode (hot-reloading the frontend via Vite) is **not** available
    in Docker — Caddy serves a production frontend build, so there's nothing
    to run in "dev mode"
    inside the container. See `web/frontend/README.md` for the (non-Docker)
    dev-mode workflow if you want to contribute to the frontend.

### Mounting volumes for persistent data

The container's filesystem is ephemeral by default — uploaded evidence
spreadsheets and any CLI-generated output disappear when it's removed. Mount
host directories in with `-v` to persist them across restarts:

```bash
docker run --rm \
  -p 8000:8000 \
  -v "$(pwd)/uploads:/opt/mapwisefox/uploads" \
  -v "$(pwd)/data:/opt/mapwisefox/data" \
  ghcr.io/koosie0507/mapwisefox:latest
```

- `/opt/mapwisefox/uploads` is the web app's upload directory
  (`MWF_WEB_UPLOADS_DIR`, defaulting to `<basedir>/uploads`) — this is
  where spreadsheets uploaded through the UI are written and read back
  from. You may use this as the `--data-dir` of the other CLIs (e.g.
  `search`).
- `/opt/mapwisefox/data` is provided as an example of how one would use
  a separate `--data-dir` to prevent mixing transient CLI outputs with
  the actual (often deduplicated) search results that must be curated by
  a human.

You can mount as many extra volumes as you like — nothing about the image
requires these two specific paths, they're just the ones tailored to the
CLI and web app defaults.

### Environment variables

Every workspace `.env` variable described [above](#environment-variables-and-env)
works the same way inside the container — pass them individually with `-e`,
or point at your existing `.env` file with `--env-file`:

```bash
docker run --rm -p 8000:8000 \
  --env-file .env \
  -e MWF_WEB_AUTH_ENABLED=true \
  ghcr.io/koosie0507/mapwisefox:latest
```

The web application additionally reads `MWF_WEB_*` settings.

### Running other suite tools instead of the web app

The image's Python virtualenv is built with `uv sync --all-packages`, so
**every** workspace package's console script is on `PATH` inside the
container, not just `web`. Override the default command
(`CMD ["serve"]`) by appending your own after the image name:

| Command          | Package                        |
| ---------------- | ------------------------------ |
| `serve`          | Web UI and API (the default)   |
| `web`            | `web/backend` API only         |
| `search`         | [`search`](../search/index.md) |
| `deduplicate`    | [`deduplication`](../deduplication/index.md) |
| `metrics`        | `metrics`                      |
| `assistant`      | `assistant`                    |
| `snowball`       | `snowballing`                  |
| `split-workload` | `split`                        |

For example, running a search config through the same image, with the
config file and its base data directory both mounted in:

```bash
docker run --rm \
  --env-file .env \
  -v "$(pwd)/search/config.example.yaml:/opt/mapwisefox/config.yaml:ro" \
  -v "$(pwd)/data:/opt/mapwisefox/data" \
  ghcr.io/koosie0507/mapwisefox:latest \
  search --config ./config.yaml --data-dir ./data
```

### Building the image yourself

```bash
docker build -t mapwisefox:local .
```

The image builds every Python workspace package with `uv` and the standalone
React app with npm. Caddy serves the frontend and proxies backend routes to the
FastAPI process in the same container.

## Local development

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.13+ (uv will fetch a matching interpreter automatically if you
  don't have one)
- Node.js, only if you're working on `web/frontend` (see
  [Web frontend](#web-frontend) below)

### Clone and sync

```bash
git clone https://github.com/koosie0507/mapwisefox.git
cd mapwisefox
uv sync
```

`uv sync` resolves and installs **every** workspace member into one shared
`.venv`, using the root [`uv.lock`](https://docs.astral.sh/uv/concepts/projects/workspaces/)
for reproducibility. There's no need to `cd` into a package and sync it
separately — everything is available from the repo root via
`uv run <command>` or `uv run --package <name> <command>`.

### Workspace members

| Package                        | What it does                                                        |
| ------------------------------ | ------------------------------------------------------------------- |
| [`search`](../search/index.md) | DSL + CLI for querying multiple academic search APIs from one query |
| [`deduplication`](../deduplication/index.md) | Merges and deduplicates results from multiple sources               |
| [`split`](../split/index.md) | Divides review workbooks among reviewers                              |
| [`metrics`](../metrics/index.md) | Review-quality and coverage metrics                                |
| [`assistant`](../assistant/index.md) | LLM-assisted review helpers                                     |
| [`snowballing`](../snowballing/index.md) | Citation snowballing                                        |
| [`web/backend`](../web/index.md) | API backend for the web UI                                         |
| `web/frontend`                 | React/TypeScript web UI — **not** a uv workspace member (see below) |

Each documented tool has its own section with tool-specific setup and usage.
This page covers the workspace setup they share.

### Environment variables and `.env`

Packages that need secrets (API keys, etc.) load a `.env` file automatically
via [`python-dotenv`](https://pypi.org/project/python-dotenv/), which walks
upward from the location of the module that calls `load_dotenv()` looking for
a `.env` file — so a single `.env` at the repo root is found and covers every
package, regardless of which one you're running from:

```dotenv
# .env, at the repo root — never commit real values
MWF_SEARCH_ELSEVIER_API_KEY=...
MWF_SEARCH_SPRINGER_API_KEY=...
MWF_SEARCH_CLARIVATE_API_KEY=...
```

`.env*` is already gitignored at the repo root. See each package's own
"Getting Started" page for the specific variables it needs — for example,
[Search → Installation](../search/getting-started/installation.md#api-keys)
for its per-backend API keys.

### Dev tooling

The root [`pyproject.toml`](https://github.com/koosie0507/mapwisefox/blob/main/pyproject.toml)
defines a `dev` dependency group shared by the whole workspace
(`black`, `ruff`, `mypy`, `pytest`, `memray`):

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
```

### Building these docs

This site itself is built with [MkDocs](https://www.mkdocs.org/) +
[Material](https://squidfunk.github.io/mkdocs-material/), via a `docs`
dependency group:

```bash
uv sync --group docs
uv run mkdocs serve
```

### Web frontend

`web/frontend` is a Vite + React + TypeScript app, managed with npm rather
than uv — it's intentionally outside the uv workspace since it isn't a
Python package:

```bash
cd web/frontend
npm install
npm run dev
```
