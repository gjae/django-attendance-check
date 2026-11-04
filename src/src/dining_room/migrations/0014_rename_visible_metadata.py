# Migración de metadatos para la iteración de renombrado visible del comedor:
#
# - GhostEmployee ahora se denomina "Procedencia" (se remueve la palabra
#   "fantasma" de la interfaz de usuario).
# - GhostServiceLoad ahora se denomina "Totalización de servicios".
# - El help_text de la fecha de la carga pasa a formato DD/MM/AAAA.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dining_room", "0013_ghostemployee_ghostserviceload"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ghostemployee",
            options={
                "ordering": ["name"],
                "verbose_name": "Procedencia",
                "verbose_name_plural": "Procedencias",
            },
        ),
        migrations.AlterModelOptions(
            name="ghostserviceload",
            options={
                "ordering": ["-date_day", "created"],
                "verbose_name": "Totalización de servicios",
                "verbose_name_plural": "Totalización de servicios",
            },
        ),
        migrations.AlterField(
            model_name="ghostemployee",
            name="name",
            field=models.CharField(
                help_text=(
                    "Nombre corto que identifica la procedencia del beneficio cargado "
                    "(ej: 'Visita Casa Matriz')"
                ),
                max_length=255,
                verbose_name="Nombre / procedencia",
            ),
        ),
        migrations.AlterField(
            model_name="ghostserviceload",
            name="date_day",
            field=models.DateField(
                db_index=True,
                help_text="Formato: DD/MM/AAAA",
                verbose_name="Día de la carga",
            ),
        ),
    ]
