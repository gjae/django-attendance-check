# Generated by Django 4.2.6 on 2024-06-10 23:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0012_employee_is_removed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employee",
            name="cedula",
            field=models.PositiveIntegerField(db_index=True, default=0, unique=True, verbose_name="Cédula"),
        ),
    ]
