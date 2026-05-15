FROM debian:stable-slim AS model-fetch
RUN apt-get update -yqq \
 && apt-get install -yqq --no-install-recommends curl ca-certificates file \
 && rm -rf /var/lib/apt/lists/*

# Pinned upstream. Override at build time with --build-arg if you mirror it.
ARG PUBLAYNET_URL="https://huggingface.co/layoutparser/efficientdet/resolve/main/PubLayNet/tf_efficientdet_d1/publaynet-tf_efficientdet_d1.pth.tar"
# Compute once on a known-good local copy:  sha256sum publaynet-tf_efficientdet_d1.pth.tar?dl=1
# Then hardcode it here so a future Dropbox HTML page can't slip through.
ARG PUBLAYNET_SHA256=""

WORKDIR /out
RUN set -eux; \
    target="publaynet-tf_efficientdet_d1.pth.tar"; \
    echo ">>> fetching ${PUBLAYNET_URL}"; \
    curl \
        --proto '=https' --tlsv1.2 \
        --location \
        --fail --show-error \
        --retry 8 --retry-delay 3 --retry-all-errors \
        --connect-timeout 15 --max-time 900 \
        --continue-at - \
        -A "Mozilla/5.0 (X11; Linux x86_64) mapwisefox-docker-build/1.0" \
        -H "Accept: application/octet-stream, */*" \
        -o "${target}" \
        "${PUBLAYNET_URL}"; \
    \
    # --- Sanity gate #1: not HTML / XML / text ---
    first_byte_hex="$(head -c 1 "${target}" | od -An -tx1 | tr -d ' \n')"; \
    if [ "${first_byte_hex}" = "3c" ]; then \
        echo "ERROR: downloaded file starts with '<' — most likely URL is GONE."; \
        echo "----- first 400 bytes -----"; head -c 400 "${target}"; echo; \
        exit 1; \
    fi; \
    detected="$(file -b "${target}")"; \
    echo "file(1) says: ${detected}"; \
    case "${detected}" in \
      *HTML*|*XML*|*"ASCII text"*|*"empty"*) \
          echo "ERROR: not a binary checkpoint (${detected})"; exit 1 ;; \
    esac; \
    \
    # --- Sanity gate #2: optional but strongly recommended checksum ---
    if [ -n "${PUBLAYNET_SHA256}" ]; then \
        echo "${PUBLAYNET_SHA256}  ${target}" | sha256sum -c -; \
    else \
        echo "WARNING: PUBLAYNET_SHA256 not set; skipping checksum verification."; \
    fi; \
    \
    # --- Place at the exact path iopath will look up ---
    # Dropbox handler caches as: <cache_dir>/s/<id>/<filename>?dl=1
    mkdir -p "/out/cache/s/gxy11xkkiwnpgog"; \
    mv "${target}" "/out/cache/s/gxy11xkkiwnpgog/publaynet-tf_efficientdet_d1.pth.tar?dl=1"; \
    ls -la "/out/cache/s/gxy11xkkiwnpgog/"


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

RUN apt update -yqq && apt install libgomp1 libstdc++6 ffmpeg libsm6 libxext6 poppler-utils -yqq && \
    useradd -u 1001 -r -s /bin/sh -d /opt/mapwisefox mapwisefox && \
    mkdir -p uploads .cache && \
    chown -R mapwisefox:users /opt/mapwisefox && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# iopath default cache dir is $HOME/.torch/iopath_cache
# mapwisefox's HOME is /opt/mapwisefox
COPY --from=model-fetch --chown=mapwisefox:users \
     /out/cache /opt/mapwisefox/.torch/iopath_cache


COPY --from=python-runtime --chown=mapwisefox:mapwisefox /opt/mapwisefox/.venv .venv
COPY --from=python-runtime --chown=mapwisefox:mapwisefox /opt/mapwisefox/web/assets assets
COPY --from=node-build --chown=mapwisefox:mapwisefox /opt/node-build/assets assets/

USER mapwisefox
CMD ["web"]
