---
title: Web operations and configuration
description: Run MapwiseFox Web locally or in production and configure storage and optional OIDC authentication.
tags:
- web
- configuration
- deployment
---

# Web operations and configuration

You can run the FastAPI backend and Vite frontend separately during local development. In production, the packaged application serves both from one public origin through Caddy.

## Local development

Install the shared Python environment and frontend dependencies from the repository root. See [workspace installation](../getting-started/installation.md) for prerequisites.

Start the backend from the repository root:

```bash
uv run web --host 127.0.0.1 --port 8000
```

In a second terminal, start the frontend:

```bash
cd web/frontend
npm run dev
```

Open <http://localhost:5173>. Vite runs on port `5173` and proxies `/api` and `/auth` requests to the backend at `http://localhost:8000`.

!!! tip
    Run `make bootstrap` once to create the Python environment and install frontend dependencies together.

## Production behavior

The production image builds the frontend into static files. Caddy serves those files on port `8000` and proxies `/api/*`, `/auth/*`, `/docs*`, `/redoc*`, and `/openapi.json` to FastAPI on `127.0.0.1:8001`.

This same-origin setup keeps browser requests and authentication callbacks on one public origin. Preserve those routes when you place the application behind another proxy.

Run the published image locally with persistent uploads:

```bash
docker run --rm -p 8000:8000 \
  -v "$(pwd)/uploads:/opt/mapwisefox/uploads" \
  ghcr.io/koosie0507/mapwisefox:latest
```

Open <http://localhost:8000>. See [workspace installation](../getting-started/installation.md#docker) for image build and volume details.

## Configuration

The backend reads environment variables with the `MWF_WEB_` prefix. Set them in the service environment or in the repository-root `.env` file for local work. Do not commit secrets.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MWF_WEB_AUTH_ENABLED` | `false` | Enables OpenID Connect (OIDC) login and per-user upload directories. |
| `MWF_WEB_UPLOADS_DIR` | `uploads` in the current directory | Directory for uploaded workbooks and, by default, the OIDC cache file. Make it persistent and writable. |
| `MWF_WEB_DECISION_COLUMN` | `include` | Workbook column that stores `include`, `exclude`, or blank decisions. |
| `MWF_WEB_EXCLUSION_REASON_COLUMN` | `exclude_reason` | Workbook column that stores exclusion-reason labels, separated by semicolons. |
| `MWF_WEB_OIDC_DISCOVERY_URL` | unset | HTTPS OIDC discovery document URL. Required when authentication is enabled. |
| `MWF_WEB_OIDC_CLIENT_ID` | unset | OIDC client ID. Required when authentication is enabled. |
| `MWF_WEB_OIDC_CLIENT_SECRET` | unset | OIDC client secret. Required when authentication is enabled. |
| `MWF_WEB_PUBLIC_URL` | unset | Public application origin, such as `https://screening.example.org`. Required when authentication is enabled. |
| `MWF_WEB_ALLOWED_ORIGINS` | empty | Comma-separated extra browser origins allowed for authenticated requests. |
| `MWF_WEB_TOKEN_SECRET` | unset | Secret used to sign application tokens. Required when authentication is enabled. |
| `MWF_WEB_OIDC_CACHE_PATH` | `<uploads-dir>/.oidc-cache.json` | Path for cached OIDC metadata and login state. |

Set the decision and exclusion-reason column names before uploading a workbook. They are recorded for that imported survey. The names must differ and cannot replace mapped evidence columns.

## Optional OIDC authentication

Authentication is disabled by default. When it is enabled, every web user must log in through the configured OIDC provider. Each authenticated user receives a separate uploads subdirectory.

Provide all required settings:

```dotenv title=".env"
MWF_WEB_AUTH_ENABLED=true
MWF_WEB_OIDC_DISCOVERY_URL=https://login.example.org/.well-known/openid-configuration
MWF_WEB_OIDC_CLIENT_ID=mapwisefox-web
MWF_WEB_OIDC_CLIENT_SECRET=replace-with-client-secret
MWF_WEB_PUBLIC_URL=https://screening.example.org
MWF_WEB_TOKEN_SECRET=replace-with-a-random-secret-of-at-least-32-characters
MWF_WEB_ALLOWED_ORIGINS=https://screening-admin.example.org
```

Register the callback URL `<public-url>/auth/callback` with your provider. The provider must support the `openid`, `profile`, and `email` scopes.

!!! warning
    Use HTTPS for `MWF_WEB_PUBLIC_URL`, the OIDC discovery URL, and allowed origins outside local development. `MWF_WEB_PUBLIC_URL` must be an origin only: do not add a path, query string, or fragment. Keep the client secret, token secret, uploads directory, and OIDC cache private. The token secret must contain at least 32 characters.

`localhost` and `127.0.0.1` are allowed for local HTTP development. Production OIDC discovery endpoints must use HTTPS.
