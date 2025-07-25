# Generated by Django 4.2.6 on 2025-07-07 16:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("peladoydescabezado", "0018_person_is_actived"),
        ("employees", "0018_employee_is_actived"),
        ("dining_room", "0011_alter_confdiningroom_managers"),
    ]

    operations = [
        migrations.AddField(
            model_name="diningchecking",
            name="person",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dining_room_checkings",
                to="peladoydescabezado.person",
            ),
        ),
        migrations.AlterField(
            model_name="diningchecking",
            name="employer",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dining_room_checkings",
                to="employees.employee",
            ),
        ),
    ]
