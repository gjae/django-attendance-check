# Generated by Django 4.2.6 on 2024-01-21 11:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clocking", "0009_dailycalendarobservation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dailycalendarobservation",
            name="support",
            field=models.FileField(
                default=None, null=True, upload_to="uploads/dailycalendarsupports/", verbose_name="Soporte"
            ),
        ),
    ]