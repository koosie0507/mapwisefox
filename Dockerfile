FROM alpine:3.22 as base
LABEL authors="Andrei Olar"
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ENV UV_INSTALL_DIR=/usr/local/bin
RUN apk add --update --no-cache python3 py3-pip py3-setuptools git &&\
    ln -sf python3 /usr/bin/python && \
    wget -qO- https://astral.sh/uv/install.sh | sh

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=web/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY web/ /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable


FROM alpine:3.22 as runtime
LABEL authors="Andrei Olar"

EXPOSE 8000
WORKDIR /app
ENV PATH="$PATH:/app/.venv/bin"

COPY --from=base --chown=app:app /app/.venv /app/.venv

CMD ["web"]
