# Generated by Django 5.0.4 on 2024-04-15 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0025_alter_knownclient_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpreferences',
            name='dark_mode',
            field=models.IntegerField(choices=[(0, 'Dunkles Design'), (1, 'Helles Design'), (2, 'Wie Betriebssystem')], default=1, verbose_name='Dunkles Design'),
        ),
    ]