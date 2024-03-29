# Generated by Django 4.2.6 on 2024-01-21 11:28

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0009_alter_employee_department_alter_employee_position"),
        ("clocking", "0008_alter_dailychecks_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyCalendarObservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("description", models.TextField(verbose_name="Descripción")),
                ("support", models.FileField(upload_to="uploads/dailycalendarsupports/", verbose_name="Soporte")),
                (
                    "calendar_day",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="observations",
                        to="clocking.dailycalendar",
                        verbose_name="Día del calendario",
                    ),
                ),
                (
                    "employer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="calendar_observations",
                        to="employees.employee",
                        verbose_name="Trabajador",
                    ),
                ),
            ],
            options={
                "verbose_name": "Observación de chequeo",
                "verbose_name_plural": "Observaciones de chequeos",
            },
        ),
    ]
