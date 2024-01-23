from django.db import models
from model_utils.models import TimeStampedModel
from model_utils.fields import StatusField
from model_utils import Choices

from src.employees.managers import EmployerManager
from src.settings.models import Department


# Create your models here.
class EmployeePosition(TimeStampedModel):
    position = models.CharField(
        "Cargo",
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
    date_entry_job = models.DateField("Fecha de ingreso", null=True, default=None, help_text="Formato: AAAA-MM-DD")
    birthday_at = models.DateField("Fecha de nacimiento", null=True, default=None, help_text="Formato: AAAA-MM-DD")

    position = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE, related_name="employees", null=True, default=None, verbose_name="Cargo")

    status = StatusField(default="actived")
    department = models.ForeignKey(Department, on_delete=models.RESTRICT, related_name="employers", null=True, default=None, verbose_name="Departamento")
    objects = EmployerManager()
    deleted_at = models.DateTimeField("Eliminado", null=True, default=None)

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"
        ordering = ["date_entry_job", ]


    def __str__(self):
        return f"{self.get_fullname()} - {self.cedula}"


    def get_fullname(self):
        return f"{self.last_name}, {self.name}"
    

    @property
    def allow_checking(self) -> bool:
        if self.status == Employee.STATUS.rejected:
            return False
        

        return True