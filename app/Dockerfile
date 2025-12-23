FROM docker.io/oven/bun:1-slim AS base
WORKDIR /usr/src/app

FROM base AS install
RUN mkdir -p /temp/dev
COPY bundle/package.json bundle/bun.lock /temp/dev/
RUN cd /temp/dev && bun install --frozen-lockfile

RUN mkdir -p /temp/prod
COPY bundle/package.json bundle/bun.lock /temp/prod/
RUN cd /temp/prod && bun install --frozen-lockfile --production

FROM base AS prerelease
COPY --from=install /temp/dev/node_modules node_modules
COPY ./bundle .

ENV NODE_ENV=production
RUN bun test
RUN bun run build --minify --production

FROM stagybee/python-base:slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV DEPENDENCIES="gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libc-dev"

RUN apt-get update && apt-get install -y --no-install-recommends gettext libpq5 netcat-openbsd $DEPENDENCIES && \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --only-dev --extra postgres && \
    apt-get autoremove -y --purge $DEPENDENCIES && \
    rm -rf /var/lib/apt/lists/*

COPY --from=prerelease --chown=pyuser:users /StagyBee/static $TMP/StagyBee/static
COPY --chown=pyuser:users ./scripts/entrypoint.sh /opt/StagyBee/

ENTRYPOINT ["/opt/StagyBee/entrypoint.sh"]