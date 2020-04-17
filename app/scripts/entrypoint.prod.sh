#!/usr/bin/env sh

if [ -e ".env" ]; then
    ENV_SQL_ENGINE="$(grep SQL_ENGINE .env | cut -d '=' -f2)"
    SQL_ENGINE="${ENV_SQL_ENGINE:-django.db.backends.sqlite}"
    if [ "${SQL_ENGINE}" = "django.db.backends.postgresql" ]; then
      ENV_SQL_HOST="$(grep SQL_HOST .env | cut -d '=' -f2)"
      SQL_HOST="${ENV_SQL_HOST:-localhost}"
      ENV_SQL_PORT="$(grep SQL_PORT .env | cut -d '=' -f2)"
      SQL_PORT="${ENV_SQL_PORT:-5678}"
    fi
fi

if [ "${SQL_ENGINE}" = "django.db.backends.postgresql" ]; then
    echo "Waiting for postgres..."

    while ! nc -z "${SQL_HOST}" "${SQL_PORT}"; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py migrate --no-input
python manage.py compilemessages --ignore venv
python manage.py collectstatic --no-input --clear

exec "$@"