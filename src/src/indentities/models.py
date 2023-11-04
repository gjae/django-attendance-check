from django.db import models
from datetime import timedelta
from django.utils import timezone
from model_utils.models import TimeStampedModel
from model_utils import Choices


from src.employees.models import Employee
class Identity(TimeStampedModel):
    STATUS = Choices(
        (0, "actived", "Activo"),
        (1, "expired", "Caducado"),
        (2, "disabled", "Desactivado")
    )

    status = models.IntegerField(
        "Estado del carnet",
        choices=STATUS,
        default=STATUS.actived
    )

    employer = models.ForeignKey(
        Employee,
        on_delete=models.RESTRICT,
        related_name="identities",
        verbose_name="Carnet del trabajador"
    )

    emited_at = models.DateTimeField(
        "Fecha de emisión",
        auto_now_add=True
    )

    expire_at = models.DateTimeField(
        "Fecha de expiración"
    )
    
    expirable = models.BooleanField(
        "Caduca",
        default=True,
        help_text=(
            "Si esta opción esta activada, el carne expirará en la fecha establecioda (1 años a partir de la fecha) "
            "por defecto está activada"
        )
    )

    class Meta:
        verbose_name = "Carnet"
        verbose_name_plural = "Carnets"


    def __str__(self):
        return f"Identificación del trabajador {self.employer.get_fullname()}"
    
    def save(self):
        self.emited_at = timezone.now()
        self.expire_at = self.emited_at + timedelta(days=366)

        return super().save()