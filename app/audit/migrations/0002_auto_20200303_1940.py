# Generated by Django 3.0.3 on 2020-03-03 18:40

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audit',
            name='send_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
