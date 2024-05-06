# Generated by Django 5.0.4 on 2024-04-19 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0026_alter_userpreferences_dark_mode'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userpreferences',
            name='dark_mode',
        ),
        migrations.AddField(
            model_name='userpreferences',
            name='design',
            field=models.IntegerField(choices=[(0, 'Dunkles Design'), (1, 'Helles Design'), (2, 'Wie Betriebssystem')], default=1, verbose_name='Erscheinungsbild'),
        ),
    ]