# Generated by Django 4.0 on 2021-12-16 13:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0003_notification_show_in_locale_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'ordering': ['-create_date', '-importance']},
        ),
    ]