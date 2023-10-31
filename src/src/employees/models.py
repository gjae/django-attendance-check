from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.fields import StatusField
from model_utils import Choices

from src.employees.managers import EmployerManager


# Create your models here.
class EmployeePosition(TimeStampedModel):
    position = models.CharField(
        "Cago",
        max_length=255
    )

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"

    def __str__(self):
        return self.position


class Employee(TimeStampedModel):
    STATUS = Choices(
        ('actived', "Activo"), 
        ('suspended', "Suspendido"), 
        ('rejected', "Expulsado")
    )
    name = models.CharField("Nombre", blank=True, max_length=255)
    last_name = models.CharField("Apellido", blank=True, max_length=255, default='') 
    cedula = models.PositiveIntegerField("Cédula", db_index=True, default=0)
    picture = models.ImageField("Foto", upload_to='pictures')
    date_entry_job = models.DateField("Fecha de ingreso", null=True, default=None)

    position = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE, related_name="employees", null=True, default=None)

    status = StatusField(default="actived")
    objects = EmployerManager()

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"
        ordering = ["date_entry_job", ]


    def __str__(self):
        return f"{self.get_fullname()} - {self.cedula}"


    def get_fullname(self):
        return f"{self.name} {self.last_name}"
    

    @property
    def allow_checking(self) -> bool:
        if self.status == Employee.STATUS.rejected:
            return False
        

        return True