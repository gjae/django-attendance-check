from django.db import models
from model_utils.models import TimeStampedModel, StatusModel
from model_utils import Choices
from model_utils.fields import StatusField

from src.settings.managers import ClientConfigManager, DepartmentManager
from src.settings.querysets import DepartmentQuerySet

# Create your models here.
class ClientConfig(TimeStampedModel, StatusModel):
    STATUS = Choices(
        ("enabled", "Activo"),
        ("disabled", "Desactivado")
    )

    client_ip = models.CharField(
        "IP del cliente",
        max_length=24,
        db_index=True
    )

    description = models.CharField(
        "Título",
        max_length=70
    )

    note = models.TextField(
        "Observación",
        blank=True,
        default=''
    )

    objects = ClientConfigManager()

    class Meta:
        verbose_name = "Punto de entrada"
        verbose_name_plural = "Puntos de entrada"

    def __str__(self):
        return f"{self.description} - {self.client_ip}"
    


class Department(TimeStampedModel):
    name = models.CharField(
        "Nombre",
        max_length=150
    )

    is_actived = models.BooleanField(
        "Departamento activo",
        default=True
    )

    objects = DepartmentManager.from_queryset(DepartmentQuerySet)()

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

    
    def __str__(self):
        return self.name