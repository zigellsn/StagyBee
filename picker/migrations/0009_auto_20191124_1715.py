# Generated by Django 2.2.7 on 2019-11-24 16:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('picker', '0008_credential_display_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='credential',
            options={'ordering': ['display_name', 'congregation']},
        ),
    ]
