# Generated by Django 3.0.7 on 2020-07-05 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0002_notification_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='locale',
            field=models.CharField(default='en', max_length=10),
        ),
    ]
