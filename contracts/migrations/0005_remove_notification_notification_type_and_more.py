# Generated by Django 5.1.6 on 2025-03-15 10:35

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contracts", "0004_contract_supervisor_alter_contract_contract_name_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="notification",
            name="notification_type",
        ),
        migrations.RemoveField(
            model_name="notification",
            name="recipient_phone",
        ),
        migrations.AddField(
            model_name="notification",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="notification",
            name="recipient",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="notifications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="contract",
            name="staff_name",
            field=models.CharField(default="Unknown", max_length=255),
        ),
        migrations.AlterField(
            model_name="notification",
            name="sent_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="unit",
            name="name",
            field=models.CharField(default="Unknown", max_length=100),
        ),
    ]
