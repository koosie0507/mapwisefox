FROM alpine:3.22 AS base
LABEL authors="Andrei Olar"
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ENV UV_INSTALL_DIR=/usr/local/bin
RUN apk add --update --no-cache python3 py3-pip py3-setuptools git &&\
    ln -sf python3 /usr/bin/python && \
    wget -qO- https://astral.sh/uv/install.sh | sh

COPY uv.lock uv.lock
COPY web/pyproject.toml pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-editable

COPY web/ /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-editable


FROM alpine:3.22 AS runtime
LABEL authors="Andrei Olar"

EXPOSE 8000
WORKDIR /app
ENV PATH="$PATH:/app/.venv/bin"

RUN apk add --update --no-cache python3
COPY --from=base --chown=app:app /app/.venv /app/.venv
COPY --from=base --chown=app:app /app/src/mapwisefox/web/static/ /app/.venv/lib/python3.12/site-packages/mapwisefox/web/static/
COPY --from=base --chown=app:app /app/src/mapwisefox/web/view/templates /app/.venv/lib/python3.12/site-packages/mapwisefox/web/view/templates

CMD ["web"]
