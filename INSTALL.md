# Installation

Install [Python 3.8](https://www.python.org/) and [gettext](https://www.gnu.org/software/gettext/gettext.html) if necessary.
Install and configure [Redis](https://redis.io/) if necessary.

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

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --run-syncdb
python manage.py createsuperuser
python manage.py compilemessages
python manage.py collectstatic
python manage.py runserver
```

Log on to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) with the created super user.
Create the required credential data sets.

## Running in production

Copy the file .env.example to .env and adjust to your needs.
``` bash
cp .env.example .env
```

Change the value of DEBUG in .env to False, and don't forget to set the SECRET_KEY value!

To run StagyBee in a production setting use
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --run-syncdb
python manage.py createsuperuser
python manage.py compilemessages
python manage.py collectstatic
daphne -b 0.0.0.0 -p 8000 stagy_bee.asgi:application
```

Log on to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) with the created super user.
Create the required credential data sets.

For running StagyBee in production additional steps might be necessary, e.g. using and configuring nginx as reverse proxy.
Refer to the examples at [https://docs.djangoproject.com/](https://docs.djangoproject.com/en/3.0/howto/deployment/) for guidance.

## Usage

Open [http://127.0.0.1:8000/picker/](http://127.0.0.1:8000/picker/). E.g.:
```bash
chromium-browser --incognito --kiosk http://127.0.0.1:8000/picker/
```

## Use shutdown and reboot scripts

```bash
chmod +x shutdown.sh
```