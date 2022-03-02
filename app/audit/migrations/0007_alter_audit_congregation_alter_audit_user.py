# Generated by Django 4.0.3 on 2022-03-01 10:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('picker', '0020_alter_credential_extractor_url'),
        ('audit', '0006_alter_audit_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audit',
            name='congregation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audits', to='picker.credential'),
        ),
        migrations.AlterField(
            model_name='audit',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audits', to=settings.AUTH_USER_MODEL),
        ),
    ]
