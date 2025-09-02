FROM alpine:3.22 AS base
LABEL authors="Andrei Olar"
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ENV UV_INSTALL_DIR=/usr/local/bin
RUN apk add --update --no-cache python3 py3-pip py3-setuptools git nodejs npm &&\
    ln -sf python3 /usr/bin/python && \
    wget -qO- https://astral.sh/uv/install.sh | sh

COPY uv.lock uv.lock
COPY web/backend/pyproject.toml backend/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    (cd backend && uv sync --no-install-project --no-editable)

COPY web/ /app
RUN --mount=type=cache,target=/root/.cache/uv \
    (cd backend && uv sync --no-editable) && \
    (cd /app/frontend && npm install && npm run build)


FROM alpine:3.22 AS runtime
LABEL authors="Andrei Olar"

EXPOSE 8000
WORKDIR /app
ENV PATH="$PATH:/app/backend/.venv/bin"
ENV MWF_WEB_DEBUG=0
ENV MWF_WEB_BASEDIR="/app"

RUN apk add --update --no-cache python3
COPY --from=base --chown=app:app /app/backend/.venv /app/backend/.venv
COPY --from=base --chown=app:app /app/assets /app/assets
COPY --from=base --chown=app:app /app/backend/src/mapwisefox/web/view/templates /app/.venv/lib/python3.12/site-packages/mapwisefox/web/view/templates

CMD ["web"]
