# Migración que agrega la FK opcional work_center (Empresa,
# settings.WorkCenter) a GhostEmployee: una procedencia PUEDE estar
# relacionada a una empresa. Cuando la relación existe, los servicios
# cargados a esa procedencia (GhostServiceLoad) se suman a la
# totalización del reporte por empresa, discriminados por tipo de
# beneficio. Por defecto es null para ser genérica.

import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dining_room", "0015_ghostserviceload_procedencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="ghostemployee",
            name="work_center",
            field=models.ForeignKey(
                blank=True,
                default=None,
                help_text=(
                    "Empresa a la que corresponde la procedencia (opcional); si se "
                    "define, sus servicios cargados se suman a la totalización del "
                    "reporte por empresa, discriminados por tipo de beneficio"
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="ghost_employees",
                to="settings.workcenter",
                verbose_name="Empresa",
            ),
        ),
    ]
