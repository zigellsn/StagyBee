# Generated by Django 3.0.3 on 2020-02-18 13:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0003_auto_20200218_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeentry',
            name='start',
            field=models.DateTimeField(),
        ),
    ]
