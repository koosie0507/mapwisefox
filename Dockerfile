FROM python:3.13.7-slim AS python-build
ARG BUILD_PKGS="git build-essential"
LABEL authors="Andrei Olar <andrei.olar@gmail.com>"
ENV PYTHONUNBUFFERED=1

WORKDIR /opt/python-build

ENV UV_INSTALL_DIR=/usr/local/bin
RUN apt update -yqq && apt install ${BUILD_PKGS} -yqq

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY uv.lock uv.lock
COPY pyproject.toml pyproject.toml
COPY assistant/pyproject.toml assistant/pyproject.toml
COPY deduplication/pyproject.toml deduplication/pyproject.toml
COPY metrics/pyproject.toml metrics/pyproject.toml
COPY search/pyproject.toml search/pyproject.toml
COPY search-judge/pyproject.toml search-judge/pyproject.toml
COPY snowballing/pyproject.toml snowballing/pyproject.toml
COPY split/pyproject.toml split/pyproject.toml
RUN mkdir -p web/backend
COPY web/backend/pyproject.toml web/backend/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-workspace --no-editable --all-packages --no-dev --frozen && \
    apt remove ${BUILD_PKGS} -yqq &&\
    apt clean -yqq && \
    rm -rf /var/lib/apt/lists/*

FROM node:22.19 AS node-build

WORKDIR /opt/node-build

COPY web/frontend/package.json .
COPY web/frontend/package-lock.json .
RUN --mount=type=cache,target=/root/.npm npm install

COPY web/frontend frontend/
RUN cd frontend && npm run build

FROM python-build AS python-tests

ENV VIRTUALENV="/opt/python-build/.venv"
ENV PATH="$VIRTUALENV/bin:/root/.local/bin:$PATH"
WORKDIR "/opt/python-build"
RUN --mount=type=cache,target=/root/.cache/uv \
    adduser -u 1001 -S -D -s /bin/sh -h /opt/python-build mapwisefox && \
    uv sync --all-packages --locked

COPY . .
RUN chown -R mapwisefox /opt/python-build
USER mapwisefox

CMD ["pytest", "-q", "web/backend/tests"]

FROM python-build AS python-runtime
ARG RUNTIME_PKGS=libgomp

ENV VIRTUALENV="/opt/python-build/.venv"
ENV PATH="$VIRTUALENV/bin:/root/.local/bin:$PATH"
WORKDIR "/opt/mapwisefox"

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --all-packages --no-editable --no-dev --frozen

FROM python:3.13.7-slim
LABEL authors="Andrei Olar"

EXPOSE 8000

WORKDIR /opt/mapwisefox
ENV VIRTUALENV="/opt/mapwisefox/.venv"
ENV PATH="$VIRTUALENV/bin:$PATH"
ENV MWF_WEB_DEBUG=0
ENV MWF_WEB_BASEDIR="/opt/mapwisefox"
ENV TORCH_LOAD_WEIGHTS_ONLY=0

RUN apt update -yqq && apt install libgomp1 libstdc++6 ffmpeg libsm6 libxext6 poppler-utils -yqq && \
    useradd -u 1001 -r -s /bin/sh -d /opt/mapwisefox mapwisefox && \
    mkdir -p uploads .cache && \
    chown -R mapwisefox:users /opt/mapwisefox && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=python-runtime --chown=mapwisefox:mapwisefox /opt/mapwisefox/.venv .venv
COPY --from=python-runtime --chown=mapwisefox:mapwisefox /opt/mapwisefox/web/assets assets
COPY --from=node-build --chown=mapwisefox:mapwisefox /opt/node-build/assets assets/

USER mapwisefox
CMD ["web"]
