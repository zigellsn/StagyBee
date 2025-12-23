# Installation with Podman

Install [Podman](https://podman.io/docs/installation) and [Podman Compose](https://github.com/containers/podman-compose) if necessary.

Download and extract [this repository](https://github.com/zigellsn/StagyBee/archive/master.zip) or use
``` bash
git clone https://github.com/zigellsn/StagyBee.git
```
Change into the extracted directory.

If running on Raspberry Pi, replace the Dockerfile for "extractor" in podman-compose.yml with 'Dockerfile.rpi'.

## Running in development
Copy the file .env.podman.example to .env and adjust to your needs.
``` bash
cp app/.env.podman.example app/.env
```

Create the directories "data", "static" and "files".
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
podman-compose -f podman-compose.yml -f podman-compose.dev.yml --podman-build-args '--format docker' up -d --build
podman-compose -f podman-compose.yml -f podman-compose.dev.yml --podman-build-args '--format docker' exec web python manage.py createsuperuser
```

Log on to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) with the created superuser.
Create the required credential data sets.

To stop everything use
``` bash
podman-compose -f podman-compose.yml -f podman-compose.dev.yml --podman-build-args '--format docker' down -v
```

## Running in production
Copy the file .env.podman.example to .env and adjust to your needs.
``` bash
cp app/.env.podman.example app/.env
```

---
**Don't forget to set the SECRET_KEY value!**

---

Create the directories "data", "static" and "files".
``` bash
mkdir data
mkdir static
mkdir files
```

Provide `key.pem` and `crt.pem` files in `./nginx/certs/`

---
- **It is recommended to restrict access to the directory `./files` on file system level!**
- **It is recommended to restrict access to the directory `./nginx/certs/` on file system level!**
---

To serve over port 80, it may be necessary to add the line `net.ipv4.ip_unprivileged_port_start=80` to `/etc/sysctl.conf`

Then run
``` bash
podman-compose -f podman-compose.yml -f podman-compose.prod.yml --podman-build-args '--format docker' up -d --build
podman-compose -f podman-compose.yml -f podman-compose.prod.yml --podman-build-args '--format docker' exec web python manage.py createsuperuser
```

Log on to [http://127.0.0.1/admin/](http://127.0.0.1/admin/) with the created superuser.
Create the required credential data sets.

To stop everything use
``` bash
podman-compose -f podman-compose.yml -f podman-compose.prod.yml --podman-build-args '--format docker' down -v
```

You may have to use podman unshare to make the shared folders accessible.
``` bash
podman unshare chown -R 1000:100 static
podman unshare chown -R 1000:100 files
```

## Usage

Open [http://127.0.0.1/picker/](http://127.0.0.1/picker/) (or [http://127.0.0.1:8000/picker/](http://127.0.0.1:8000/picker/) 
in development). E.g.:
```bash
chromium-browser --incognito --kiosk http://127.0.0.1/picker/
```

## Use shutdown and reboot scripts

To hide the shutdown icon in the UI, set `SHOW_SHUTDOWN_ICON=False` in `app/.env`.
