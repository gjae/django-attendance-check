# Generated by Django 4.2.6 on 2024-07-09 23:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clocking", "0016_alter_dailychecks_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyChecksProxyModelAdmin",
            fields=[],
            options={
                "verbose_name": "Asignar chequeos",
                "verbose_name_plural": "Asignar chequeos",
                "ordering": ["-daily__date_day", "employee_id", "-id"],
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("clocking.dailychecks",),
        ),
        migrations.AlterField(
            model_name="dailychecks",
            name="checking_time",
            field=models.DateTimeField(default=None, null=True, verbose_name="Fecha de chequeo"),
        ),
    ]
