# Generated by Django 4.2.6 on 2025-06-19 23:05

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):
    dependencies = [
        ("peladoydescabezado", "0013_weightness_alter_department_options"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="weightness",
            options={"verbose_name": "Peso", "verbose_name_plural": "Pesos"},
        ),
        migrations.RemoveField(
            model_name="control",
            name="farm",
        ),
        migrations.RemoveField(
            model_name="control",
            name="pool",
        ),
        migrations.RemoveField(
            model_name="control",
            name="size",
        ),
        migrations.RemoveField(
            model_name="control",
            name="total_weight_received",
        ),
        migrations.AddField(
            model_name="control",
            name="turn",
            field=models.IntegerField(
                choices=[(0, "Diurno"), (1, "Nocturno"), (2, "Vespertino")], default=None, null=True
            ),
        ),
        migrations.AlterField(
            model_name="basketproduction",
            name="turn",
            field=models.SmallIntegerField(
                choices=[(0, "Diurno"), (1, "Nocturno"), (2, "Vespertino")], verbose_name="Categoría de la mesa"
            ),
        ),
        migrations.CreateModel(
            name="ControlDetail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "total_weight_received",
                    models.DecimalField(decimal_places=2, max_digits=7, verbose_name="Kilos de camarón recibido"),
                ),
                (
                    "control",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="details",
                        to="peladoydescabezado.control",
                    ),
                ),
                (
                    "farm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="daily_control",
                        to="peladoydescabezado.farm",
                    ),
                ),
                (
                    "pool",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="daily_control",
                        to="peladoydescabezado.pool",
                    ),
                ),
                (
                    "weightness",
                    models.ManyToManyField(related_name="control_details", to="peladoydescabezado.weightness"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
