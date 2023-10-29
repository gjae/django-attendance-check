from django.db import models
from django.utils.html import mark_safe
from model_utils.models import TimeStampedModel
from model_utils.models import MonitorField


# Create your models here.
class Employee(TimeStampedModel):
    name = models.CharField("Nombre", blank=True, max_length=255)
    last_name = models.CharField("Apellido", blank=True, max_length=255, default='') 
    cedula = models.PositiveIntegerField("Cédula", db_index=True, default=0)
    picture = models.ImageField("Foto", upload_to='pictures')
    date_entry_job = models.DateField("Fecha de ingreso", null=True, default=None)

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"
        ordering = ["date_entry_job", ]

