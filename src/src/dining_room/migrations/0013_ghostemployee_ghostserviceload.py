# Migración que agrega los modelos de "trabajadores fantasma" del comedor:
#
# - GhostEmployee: registro ligero (nombre de procedencia) de invitados o
#   personal de alta rotación que reciben el beneficio sin ser personal fijo.
# - GhostServiceLoad: control de los días y cantidades de servicios entregados
#   a trabajadores fantasma por tipo de servicio, con soporte de erratas
#   (las cargas posteriores a la original suman al total del día).

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import model_utils.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("dining_room", "0012_diningchecking_person_alter_diningchecking_employer"),
    ]

    operations = [
        migrations.CreateModel(
            name="GhostEmployee",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name="created")),
                ("modified", model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name="modified")),
                ("is_removed", models.BooleanField(default=False)),
                ("name", models.CharField(max_length=255, verbose_name="Nombre / procedencia", help_text=(
                    "Nombre corto que identifica al grupo de trabajadores fantasmas o su "
                    "procedencia (ej: 'Visita Casa Matriz')"
                ),)),
                ("is_actived", models.BooleanField(default=True, verbose_name="Activo")),
            ],
            options={
                "verbose_name": "Trabajador fantasma",
                "verbose_name_plural": "Trabajadores fantasmas",
                "ordering": ["name"],
                "abstract": False,
            },
            bases=(model_utils.models.SoftDeletableModel, models.Model),
            managers=[("objects", django.db.models.manager.Manager())],
        ),
        migrations.CreateModel(
            name="GhostServiceLoad",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name="created")),
                ("modified", model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name="modified")),
                ("is_removed", models.BooleanField(default=False)),
                (
                    "date_day",
                    models.DateField(
                        db_index=True,
                        help_text="Formato: AAAA-MM-DD",
                        verbose_name="Día de la carga",
                    ),
                ),
                ("quantity", models.PositiveIntegerField(default=0, verbose_name="Cantidad de servicios entregados")),
                ("is_errata", models.BooleanField(default=False, editable=False, verbose_name="Es errata", help_text=(
                    "Las cargas posteriores a la primera de un mismo día y tipo de "
                    "servicio se marcan como erratas y suman al total del día"
                ),)),
                ("note", models.CharField(blank=True, default="", max_length=255, verbose_name="Nota", help_text="Nota opcional (recomendada al cargar una errata)",)),
                (
                    "loaded_by",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ghost_service_loads",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Responsable de la carga",
                    ),
                ),
                (
                    "service_type",
                    models.ForeignKey(
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ghost_service_loads",
                        to="dining_room.confdiningroom",
                        verbose_name="Tipo de servicio",
                    ),
                ),
            ],
            options={
                "verbose_name": "Carga de servicios fantasma",
                "verbose_name_plural": "Cargas de servicios fantasma",
                "ordering": ["-date_day", "created"],
                "abstract": False,
            },
            bases=(model_utils.models.SoftDeletableModel, models.Model),
            managers=[("objects", django.db.models.manager.Manager())],
        ),
    ]
