# Installation with Docker

Install [Docker](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/) if necessary.

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
```

Then run
``` bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

Log on to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) with the created super user.
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
```

Then run
``` bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Log on to [http://127.0.0.1/admin/](http://127.0.0.1/admin/) with the created super user.
Create the required credential data sets.

To stop everything use
``` bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```
## Usage

Open [http://127.0.0.1/picker/](http://127.0.0.1/picker/) (or [http://127.0.0.1:8000/picker/](http://127.0.0.1:8000/picker/) 
in development). E.g.:
```bash
chromium-browser --incognito --kiosk http://127.0.0.1:8000/picker/
```

## Use shutdown and reboot scripts

---
**DON'T USE SHUTDOWN SCRIPTS WHEN USING ONE SERVER FOR MULTIPLE INSTANCES SIMULTANEOUSLY!**

To hide the shutdown icon in the UI, set **SHOW_SHUTDOWN_ICON=False** in app/.env.

---

Install inotify-tools if necessary.

Set variable SHUTDOWN_SIGNAL in app/shutdown_interface.sh to the full path of the file app/shutdown_signal.

Then run
``` bash
sudo cp app/scripts/shutdown_interface.sh /usr/bin/
sudo cp app/scripts/shutdown_stagybee.service /etc/systemd/system/
sudo systemctl start shutdown_stagybee.service
sudo systemctl enable shutdown_stagybee.service
```