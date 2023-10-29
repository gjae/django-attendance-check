# Generated by Django 4.2.6 on 2023-10-29 14:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0002_employeeposition"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="position",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="employees",
                to="employees.employeeposition",
            ),
        ),
    ]
