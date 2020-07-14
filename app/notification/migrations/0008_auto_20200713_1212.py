# Generated by Django 3.0.7 on 2020-07-13 10:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notification', '0007_auto_20200712_1816'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='max_duration',
            field=models.DateField(blank=True, null=True, verbose_name='Gültig bis'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
