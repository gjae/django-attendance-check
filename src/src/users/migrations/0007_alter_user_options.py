# Generated by Django 4.2.6 on 2023-11-03 03:30

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_remove_user_cedula_remove_user_date_entry_job_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={"verbose_name": "Usuario", "verbose_name_plural": "Usuarios"},
        ),
    ]
