# Generated by Django 4.2.6 on 2025-04-08 22:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0013_alter_carnetmodels_back_path_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="carnetmodels",
            options={"verbose_name": "Modelo", "verbose_name_plural": "Modelos de carnet"},
        ),
        migrations.AlterField(
            model_name="carnetmodels",
            name="back_path",
            field=models.ImageField(
                default=None, null=True, upload_to="carnet_models", verbose_name="Imagen posterior/logo"
            ),
        ),
    ]
