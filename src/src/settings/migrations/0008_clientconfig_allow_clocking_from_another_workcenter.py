# Generated by Django 4.2.6 on 2024-09-07 09:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0007_remove_clientconfig_woek_center_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="clientconfig",
            name="allow_clocking_from_another_workcenter",
            field=models.BooleanField(default=False, verbose_name="Permitir chequeos de empleados de otra empresa"),
        ),
    ]