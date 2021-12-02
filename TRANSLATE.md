# Translations

Run

``` bash
python manage.py makemessages --all --ignore app/* --ignore templates/registration/*
```

Edit the django.po files in StagyBee/locale/

Afterwards run

``` bash
python manage.py compilemessages --ignore app/* --ignore templates/registration/*
```