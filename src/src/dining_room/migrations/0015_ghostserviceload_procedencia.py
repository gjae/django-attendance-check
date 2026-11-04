# Migración que agrega la FK procedencia (GhostEmployee) a
# GhostServiceLoad: cada carga de totalización queda asociada a la
# procedencia correspondiente, habilitando el reporte de totalización por
# procedencia específica.

import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dining_room", "0014_rename_visible_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="ghostserviceload",
            name="procedencia",
            field=models.ForeignKey(
                default=None,
                help_text=(
                    "Procedencia (registro fantasma) a la que corresponde esta carga "
                    "de servicios; permite filtrar y totalizar el reporte por "
                    "procedencia"
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="service_loads",
                to="dining_room.ghostemployee",
                verbose_name="Procedencia",
            ),
        ),
    ]
