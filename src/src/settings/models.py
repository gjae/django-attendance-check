from django.db import models
from model_utils.models import TimeStampedModel, StatusModel
from model_utils import Choices

from src.settings.managers import ClientConfigManager

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