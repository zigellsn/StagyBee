# Generated by Django 3.0.5 on 2020-04-06 14:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0003_auto_20200406_1559'),
    ]

    operations = [
        migrations.RenameField(
            model_name='audit',
            old_name='username',
            new_name='user',
        ),
    ]
