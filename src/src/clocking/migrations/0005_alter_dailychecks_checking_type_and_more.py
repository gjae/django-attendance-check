# Generated by Django 4.2.6 on 2023-10-29 21:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0004_alter_employeeposition_options_and_more"),
        ("clocking", "0004_alter_dailychecks_options_dailychecks_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dailychecks",
            name="checking_type",
            field=models.IntegerField(
                choices=[(0, "Entrada"), (1, "Salida")], default=0, verbose_name="Tipo de checqueo"
            ),
        ),
        migrations.AlterField(
            model_name="dailychecks",
            name="employee",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="daily_checks",
                to="employees.employee",
                verbose_name="Trabajador",
            ),
        ),
    ]
