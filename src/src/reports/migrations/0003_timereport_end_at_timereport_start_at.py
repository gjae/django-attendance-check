# Generated by Django 4.2.6 on 2023-11-12 15:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0002_alter_timereport_total_hours"),
    ]

    operations = [
        migrations.AddField(
            model_name="timereport",
            name="end_at",
            field=models.DateTimeField(default=None, null=True, verbose_name="Hora de salida"),
        ),
        migrations.AddField(
            model_name="timereport",
            name="start_at",
            field=models.DateTimeField(default=None, null=True, verbose_name="Hora de entrada"),
        ),
    ]
