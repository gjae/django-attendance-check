# Generated by Django 4.2.6 on 2024-05-21 11:55

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clocking", "0013_alter_dailycalendarobservation_calendar_day_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dailycalendar",
            name="date_day",
            field=models.DateField(db_index=True, verbose_name="Calendario de chequeos"),
        ),
        migrations.AlterField(
            model_name="dailychecks",
            name="checking_type",
            field=models.IntegerField(
                choices=[(0, "Entrada"), (1, "Salida")], default=0, verbose_name="Tipo de chequeo"
            ),
        ),
    ]