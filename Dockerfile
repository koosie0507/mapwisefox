FROM python:3.13.7-alpine3.22 AS python-build
ARG BUILD_PKGS="git build-base"
LABEL authors="Andrei Olar"
ENV PYTHONUNBUFFERED=1

WORKDIR /opt/python-build

ENV UV_INSTALL_DIR=/usr/local/bin
RUN apk add --update --no-cache ${BUILD_PKGS} &&\
    wget -qO- https://astral.sh/uv/install.sh | sh

COPY uv.lock uv.lock
COPY pyproject.toml pyproject.toml
COPY deduplication/pyproject.toml deduplication/pyproject.toml
COPY metrics/pyproject.toml kappa-score/pyproject.toml
COPY search/pyproject.toml search/pyproject.toml
COPY search-judge/pyproject.toml search-judge/pyproject.toml
COPY snowballing/pyproject.toml snowballing/pyproject.toml
COPY split/pyproject.toml split/pyproject.toml
RUN mkdir -p web/backend
COPY web/backend/pyproject.toml web/backend/pyproject.toml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-workspace --no-editable --all-packages --no-dev --locked && \
    apk del ${BUILD_PKGS}

FROM node:22.19-alpine3.22 AS node-build

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
    uv sync --all-packages --no-editable --no-dev --locked 

FROM python:3.13.7-alpine3.22
LABEL authors="Andrei Olar"

EXPOSE 8000

WORKDIR /opt/mapwisefox
ENV VIRTUALENV="/opt/mapwisefox/.venv"
ENV PATH="$VIRTUALENV/bin:$PATH"
ENV MWF_WEB_DEBUG=0
ENV MWF_WEB_BASEDIR="/opt/mapwisefox"

RUN apk add libgomp libstdc++ && \
    adduser -u 1001 -S -D -s /bin/sh -h /opt/mapwisefox mapwisefox && \
    mkdir -p uploads

COPY --from=python-runtime --chown=mapwisefox:mapwisefox /opt/mapwisefox/.venv .venv
COPY --from=python-runtime --chown=mapwisefox:mapwisefox /opt/mapwisefox/web/assets assets
COPY --from=node-build --chown=mapwisefox:mapwisefox /opt/node-build/assets assets/

USER mapwisefox
CMD ["web"]
