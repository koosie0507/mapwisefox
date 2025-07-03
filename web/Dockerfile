FROM alpine:3.22 as base
LABEL authors="Andrei Olar"
ENV UV_INSTALL_DIR=/usr/local/bin
ENV PYTHONUNBUFFERED=1

RUN apk add --update --no-cache python3 py3-pip py3-setuptools git
RUN ln -sf python3 /usr/bin/python && \
    wget -qO- https://astral.sh/uv/install.sh | sh

FROM base as runtime

WORKDIR /app
ENV UV_PYTHON_PREFERENCE=only-system
ENV PATH="$PATH:/app/.venv/bin"

COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
RUN apk add --update --no-cache alpine-sdk python3-dev &&\
    uv sync --no-dev &&\
    apk del alpine-sdk python3-dev

COPY . .

ENTRYPOINT ["uv", "run"]
CMD ["web", "--help"]