# Generated by Django 4.2.6 on 2025-04-08 22:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0017_alter_transfer_employee_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="is_actived",
            field=models.BooleanField(default=True, verbose_name="Empleado activo"),
        ),
    ]
