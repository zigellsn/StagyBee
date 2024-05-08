# Generated by Django 5.0.6 on 2024-05-08 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('console', '0028_rename_design_userpreferences_scheme'),
    ]

    operations = [
        migrations.AlterField(
            model_name='knownclient',
            name='alias',
            field=models.TextField(db_default='Client', verbose_name='Alias Name'),
        ),
        migrations.AlterField(
            model_name='userpreferences',
            name='locale',
            field=models.CharField(db_default='en', max_length=10, verbose_name='Sprache'),
        ),
        migrations.AlterField(
            model_name='userpreferences',
            name='scheme',
            field=models.IntegerField(choices=[(0, 'Dunkles Design'), (1, 'Helles Design'), (2, 'Wie Betriebssystem')], db_default=1, verbose_name='Erscheinungsbild'),
        ),
    ]
