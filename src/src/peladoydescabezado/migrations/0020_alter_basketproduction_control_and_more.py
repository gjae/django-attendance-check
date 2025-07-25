# Generated by Django 4.2.6 on 2025-07-07 23:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("peladoydescabezado", "0019_alter_reportproxymodel_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="basketproduction",
            name="control",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="production",
                to="peladoydescabezado.control",
            ),
        ),
        migrations.AlterField(
            model_name="basketproduction",
            name="saved_by",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="production_saveds",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="basketproduction",
            name="worker",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="product_baskets",
                to="peladoydescabezado.person",
                verbose_name="Trabajador",
            ),
        ),
        migrations.AlterField(
            model_name="control",
            name="approved_by",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="production_control_approved",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="control",
            name="checked_by",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="production_control_checked",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="control",
            name="created_by",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="production_control_created",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="controldetail",
            name="farm",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="daily_control",
                to="peladoydescabezado.farm",
            ),
        ),
        migrations.AlterField(
            model_name="controldetail",
            name="pool",
            field=models.ForeignKey(
                default=None,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="daily_control",
                to="peladoydescabezado.pool",
            ),
        ),
    ]
