# Generated by Django 4.2.6 on 2024-09-07 09:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0008_clientconfig_allow_clocking_from_another_workcenter"),
    ]

    operations = [
        migrations.AddField(
            model_name="workcenter",
            name="is_current_center",
            field=models.BooleanField(
                default=True,
                help_text="Indica sí la instancia actual es la empresa/centro donde se encuentra actualmente",
                verbose_name="Marcar si este es el centro actual de la instancia",
            ),
        ),
    ]
