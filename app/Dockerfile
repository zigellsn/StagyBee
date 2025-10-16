FROM docker.io/node:18-slim AS build

COPY . .

RUN npm run install --prefix ./bundle && \
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

COPY pyproject.toml .
COPY uv.lock .

RUN apt-get update && apt-get install -y --no-install-recommends gettext libpq5 netcat-openbsd $DEPENDENCIES && \
    uv sync --locked --only-dev --extra postgres && \
    apt-get autoremove -y --purge $DEPENDENCIES && \
    rm -rf /var/lib/apt/lists/*

USER pyuser

COPY --from=build --chown=pyuser:users /StagyBee/static $TMP/StagyBee/static
COPY --chown=pyuser:users ./scripts/entrypoint.sh /opt/StagyBee/

ENTRYPOINT ["/opt/StagyBee/entrypoint.sh"]
