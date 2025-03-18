# Generated by Django 4.2.6 on 2025-02-16 11:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0012_carnetmodels_workcenter_carnet_model"),
    ]

    operations = [
        migrations.AlterField(
            model_name="carnetmodels",
            name="back_path",
            field=models.ImageField(default=None, null=True, upload_to="carnet_models", verbose_name="Imagen trasera"),
        ),
        migrations.AlterField(
            model_name="workcenter",
            name="carnet_model",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="work_centers",
                to="settings.carnetmodels",
                verbose_name="Modelo de carnet",
            ),
        ),
    ]
