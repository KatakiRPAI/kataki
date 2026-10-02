# Kataki in a browser: the web build, served by the engine (`kataki serve --web`). One library,
# one token; the multi-user website (`serve --hosted` behind the gateway) is infrastructure Phase 6.
FROM node:24-slim AS web
ENV ELECTRON_SKIP_BINARY_DOWNLOAD=1
WORKDIR /src/app
RUN corepack enable
COPY app/package.json app/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY app/ ./
RUN pnpm run build:web

FROM python:3.14-slim
RUN pip install --no-cache-dir uv
WORKDIR /kataki/engine
COPY engine/pyproject.toml engine/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY engine/src ./src
RUN uv sync --locked --no-dev
COPY --from=web /src/app/dist-web /kataki/web
# the library, its backups, pictures and the built-in embedding model: mount a volume here
ENV KATAKI_HOME=/data
VOLUME /data
# The engine binds 127.0.0.1 only: run with the host's network and put a TLS proxy in front.
# KATAKI_TOKEN is the one secret that opens the library; KATAKI_PORT picks the port.
CMD ["sh", "-c", "exec uv run --no-sync kataki serve --web /kataki/web --port ${KATAKI_PORT:-8765}"]
