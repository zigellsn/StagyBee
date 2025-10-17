FROM docker.io/node:24-slim AS build

COPY . .

RUN npm install --prefix ./bundle && \
    npm run build_dev --prefix ./bundle && \
    rm -rf ./bundle/node_modules

FROM stagybee/python-base:slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV DEPENDENCIES="gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libc-dev"

RUN apt-get update && apt-get install -y --no-install-recommends gettext libpq5 netcat-openbsd $DEPENDENCIES

RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --only-dev --extra postgres

RUN apt-get autoremove -y --purge $DEPENDENCIES && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build --chown=pyuser:users /StagyBee/static $TMP/StagyBee/static
COPY --chown=pyuser:users ./scripts/entrypoint.sh /opt/StagyBee/

ENTRYPOINT ["/opt/StagyBee/entrypoint.sh"]