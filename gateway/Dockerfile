# Kataki online's gateway (docs/specs/2026-10-02-kataki-online.md): accounts, the ledger, cloud
# save, the web build, and the signed proxy to `kataki serve --hosted`. Built from the repo root:
#   docker build -f gateway/Dockerfile .
FROM node:24-slim AS web
ENV ELECTRON_SKIP_BINARY_DOWNLOAD=1
WORKDIR /src/app
RUN corepack enable
COPY app/package.json app/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY app/ ./
RUN pnpm run build:web

FROM node:24-slim
WORKDIR /gateway
RUN corepack enable
COPY gateway/package.json gateway/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod
COPY gateway/src ./src
COPY gateway/migrations ./migrations
COPY --from=web /src/app/dist-web /web
# cloud snapshots: mount a volume here (object storage replaces it later; cloud.ts)
RUN mkdir -p /data/cloud && chown -R node /data
ENV NODE_ENV=production KATAKI_WEB=/web KATAKI_CLOUD_DIR=/data/cloud PORT=8787 KATAKI_BIND=0.0.0.0
USER node
EXPOSE 8787
CMD ["node", "src/main.ts"]
