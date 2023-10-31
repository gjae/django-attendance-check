# Generated by Django 4.2.6 on 2023-10-29 04:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0001_initial"),
        ("clocking", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dailychecks",
            name="user",
        ),
        migrations.AddField(
            model_name="dailychecks",
            name="employee",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="daily_checks",
                to="employees.employee",
            ),
            preserve_default=False,
        ),
    ]
