# Generated by Django 3.0.3 on 2020-02-18 14:54

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0004_auto_20200218_1445'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeentry',
            name='duration',
            field=models.IntegerField(default=300),
            preserve_default=False,
        ),
    ]
