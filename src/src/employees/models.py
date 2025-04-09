from datetime import datetime, date
from django.contrib import admin
from django.db import models
from django.contrib.auth import get_user_model
from model_utils.models import TimeStampedModel, SoftDeletableModel
from model_utils.fields import StatusField
from model_utils import Choices

from src.employees.managers import EmployerManager
from src.settings.models import Department

User = get_user_model()

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


class Employee(TimeStampedModel, SoftDeletableModel):
    STATUS = Choices(
        ('actived', "Activo"), 
        ('suspended', "Suspendido"), 
        ('rejected', "Expulsado")
    )
    name = models.CharField("Nombre", blank=True, max_length=255)
    last_name = models.CharField("Apellido", blank=True, max_length=255, default='') 
    cedula = models.PositiveIntegerField("Cédula", db_index=True, default=0, unique=True)
    picture = models.ImageField("Foto", upload_to='pictures')
    date_entry_job = models.DateField("Fecha de ingreso", null=True, default=None, help_text="Formato: AAAA-MM-DD")
    birthday_at = models.DateField("Fecha de nacimiento", null=True, default=None, help_text="Formato: AAAA-MM-DD")

    position = models.ForeignKey(EmployeePosition, on_delete=models.CASCADE, related_name="employees", null=True, default=None, verbose_name="Cargo")

    status = StatusField(default="actived")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, related_name="employers", null=True, default=None, verbose_name="Departamento")
    objects = EmployerManager()
    deleted_at = models.DateTimeField("Eliminado", null=True, default=None)
    is_actived = models.BooleanField(
        "Empleado activo",
        default=True
    )

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
    
    @property
    def is_birthday(self):
        today = date.today()

        if self.birthday_at is None:
            return False
        
        birth = self.birthday_at
        return birth.day == today.day and birth.month == today.month


class Transfer(TimeStampedModel, SoftDeletableModel):
    from_department = models.ForeignKey(
        Department,
        verbose_name="Departamento de origen",
        on_delete=models.CASCADE,
        related_name="transfers_origin",
    )

    to_department = models.ForeignKey(
        Department,
        verbose_name="Departamento destino",
        on_delete=models.CASCADE,
        related_name="transfer_destination"
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name="Empleado transferido",
        related_name="transfers"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="transfers_made",
        verbose_name="Responsable"
    )

    note = models.TextField(
        "Motivo de la transferencia"
    )

    class Meta:
        verbose_name = "Traslado"
        verbose_name_plural = "Traslado de empleados"