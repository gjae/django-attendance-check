# Generated by Django 4.2.6 on 2024-08-25 12:07

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):
    dependencies = [
        ("dining_room", "0010_diningchecking_is_removed"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="confdiningroom",
            managers=[
                ("removeds", django.db.models.manager.Manager()),
            ],
        ),
    ]
