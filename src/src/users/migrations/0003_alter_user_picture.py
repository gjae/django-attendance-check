# Generated by Django 4.2.6 on 2023-10-22 15:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_cedula_user_date_entry_job_user_picture"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="picture",
            field=models.ImageField(upload_to="pictures", verbose_name="Foto"),
        ),
    ]
