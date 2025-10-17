# Installation

Install [uv](https://docs.astral.sh/uv/) and [gettext](https://www.gnu.org/software/gettext/gettext.html) if necessary.
Install and configure [Redis](https://redis.io/) if necessary.
Install and configure [Node.js](https://nodejs.org/) if necessary.
If you don't want to use the standard SQLite database, you will need something like [PostgreSQL](https://www.postgresql.org/).

Download and extract [this repository](https://github.com/zigellsn/StagyBee/archive/master.zip) or use
``` bash
git clone https://github.com/zigellsn/StagyBee.git
```
Change into the "app" directory of the extracted directory.

## Running in development

Copy the file .env.example to .env and adjust to your needs.
``` bash
cp .env.example .env
```

StagyBee is configured to be running with a [PostgreSQL](https://www.postgresql.org/) database. 
This can be changed easily by editing the .env-File.

Prepare static files:
```bash
npm install
npm run build_dev
```

Copy the generated files to ./StagyBee/static/

```bash
uv sync --locked --only-dev # --extra postgres
uv run manage.py migrate --run-syncdb
uv run manage.py compilemessages --ignore .venv
uv run manage.py collectstatic
uv run manage.py createsuperuser
uv run manage.py runserver
```

Log on to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) with the created superuser.
Create the required credential data sets.

## Running in production

Copy the file .env.example to .env and adjust to your needs.
``` bash
cp .env.example .env
```

---
**Don't forget to set the SECRET_KEY value in .env!**

---

To run StagyBee in a production setting use
```bash
npm install
npm run build
```
Copy the generated files to ./StagyBee/static/
```bash
uv sync --locked --no-dev # --extra postgres
export DJANGO_SETTINGS_MODULE=StagyBee.settings
uv run manage.py migrate --run-syncdb
uv run manage.py compilemessages --ignore venv
uv run manage.py collectstatic
uv run manage.py createsuperuser
uv run daphne -b 0.0.0.0 -p 8000 StagyBee.asgi:application
```

Log on to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) with the created superuser.
Create the required credential data sets.

For running StagyBee in production additional steps might be necessary, e.g. using and configuring nginx as reverse proxy.
Refer to the examples at [https://docs.djangoproject.com/](https://docs.djangoproject.com/en/3.0/howto/deployment/) for guidance.

## Usage

Open [http://127.0.0.1:8000/picker/](http://127.0.0.1:8000/picker/). E.g.:
```bash
chromium-browser --incognito --kiosk http://127.0.0.1:8000/picker/
```

## Use shutdown and reboot scripts

To hide the shutdown icon in the UI, set `SHOW_SHUTDOWN_ICON=False` in `app/.env`.
