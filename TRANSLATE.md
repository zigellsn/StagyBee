# Translations

## Update translatable strings

Run

``` bash
python manage.py makemessages --all --ignore .venv/* --ignore templates/registration/* --ignore node_modules/*
```

Edit the django.po files in StagyBee/locale/

Afterwards run

``` bash
python manage.py compilemessages --ignore .venv/* --ignore templates/registration/* --ignore node_modules/*
```

## Add a new language

``` bash
python manage.py makemessages -l <language-code> --ignore .venv/* --ignore templates/registration/* --ignore node_modules/*
```
