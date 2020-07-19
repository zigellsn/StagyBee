# Generated by Django 3.0.8 on 2020-07-19 08:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(default='', max_length=255, verbose_name='Betreff')),
                ('message', models.TextField(blank=True, default='', verbose_name='Nachricht')),
                ('locale', models.CharField(default=' ', max_length=10, verbose_name='Sprache')),
                ('importance', models.IntegerField(choices=[(0, 'Information'), (1, 'Wichtig'), (2, 'Dringend'), (3, 'Warnung')], default=0, verbose_name='Wichtigkeit')),
                ('max_duration', models.DateTimeField(blank=True, null=True, verbose_name='Gültig bis')),
                ('active', models.BooleanField(verbose_name='Aktiv')),
                ('create_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['create_date'],
            },
        ),
    ]
