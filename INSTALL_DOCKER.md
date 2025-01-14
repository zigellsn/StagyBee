# Installation with Docker

Install [Docker](https://docs.docker.com/install/) (Version >= 20.10.0) and [Docker Compose](https://docs.docker.com/compose/) if necessary.

Download and extract [this repository](https://github.com/zigellsn/StagyBee/archive/master.zip) or use
``` bash
git clone https://github.com/zigellsn/StagyBee.git
```
Change into the extracted directory.

If running on Raspberry Pi, replace the Dockerfile for "extractor" in docker-compose.yml with 'Dockerfile.rpi'.

## Running in development
Copy the file .env.docker.example to .env and adjust to your needs.
``` bash
cp app/.env.docker.example app/.env
```

Create the directories "data" and "static".
``` bash
mkdir data
mkdir static
mkdir files
```

---
- **It is recommended to restrict access to the directory `./files` on file system level!**
---

Then run
``` bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

Log on to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) with the created superuser.
Create the required credential data sets.

To stop everything use
``` bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

## Running in production
Copy the file .env.docker.example to .env and adjust to your needs.
``` bash
cp app/.env.docker.example app/.env
```

---
**Don't forget to set the SECRET_KEY value!**

---

Create the directories "data" and "static".
``` bash
mkdir data
mkdir static
mkdir files
```

Provide key.pem and crt.pem files in ./nginx/certs/

---
- **It is recommended to restrict access to the directory `./files` on file system level!**
- **It is recommended to restrict access to the directory `./nginx/certs/` on file system level!**
---

Then run
``` bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Log on to [http://127.0.0.1/admin/](http://127.0.0.1/admin/) with the created superuser.
Create the required credential data sets.

To stop everything use
``` bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```
## Usage

Open [http://127.0.0.1/picker/](http://127.0.0.1/picker/) (or [http://127.0.0.1:8000/picker/](http://127.0.0.1:8000/picker/) 
in development). E.g.:
```bash
chromium-browser --incognito --kiosk http://127.0.0.1/picker/
```

## Use shutdown and reboot scripts

To hide the shutdown icon in the UI, set `SHOW_SHUTDOWN_ICON=False` in `app/.env`.
