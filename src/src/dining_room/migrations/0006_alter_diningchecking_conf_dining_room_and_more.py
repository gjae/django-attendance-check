# Generated by Django 4.2.6 on 2024-04-28 23:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("indentities", "0002_alter_identity_employer"),
        ("dining_room", "0005_alter_diningchecking_employer"),
    ]

    operations = [
        migrations.AlterField(
            model_name="diningchecking",
            name="conf_dining_room",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="checkings", to="dining_room.confdiningroom"
            ),
        ),
        migrations.AlterField(
            model_name="diningchecking",
            name="identity",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dining_room_checkings",
                to="indentities.identity",
            ),
        ),
    ]
