# Installation

Download and extract [this repository](https://github.com/zigellsn/StagyBee/archive/master.zip) or use
``` bash
git clone https://github.com/zigellsn/StagyBee.git
```
Install [Python 3.7](https://www.python.org/) and [gettext](https://www.gnu.org/software/gettext/gettext.html) if necessary.
Change into the extracted directory.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --run-syncdb
python manage.py createsuperuser
python manage.py compilemessages
python manage.py runserver
```

Log on to [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) with the created super user.
Create the required credential data sets.

Open [http://127.0.0.1:8000/picker/](http://127.0.0.1:8000/picker/). E.g.:
```bash
chromium-browser --incognito --kiosk http://127.0.0.1:8000/picker/
```