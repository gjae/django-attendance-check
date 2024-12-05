from django.db import models
from model_utils.models import TimeStampedModel, StatusModel, SoftDeletableModel
from model_utils import Choices
from model_utils.fields import StatusField

from src.settings.managers import ClientConfigManager, DepartmentManager
from src.settings.querysets import DepartmentQuerySet

# Create your models here.
class WorkCenter(TimeStampedModel, SoftDeletableModel):
    name = models.CharField(
        "Nombre de la empresa",
        max_length=70
    )

    code = models.CharField(
        "Codigo de la empresa",
        max_length=10,
        db_index=True,
        blank=True,
        default=""
    )

    main = models.BooleanField(
        "Empreza matriz/principal",
        default=False,
        help_text="Marcar opción si esta es la empresa principal del grupo"
    )

    address = models.TextField(
        "Dirección fiscal o fisica",
        blank=True, 
        default=""
    )

    is_active = models.BooleanField(
        "Indicar si la empresa continua activa",
        default=True
    )

    opened_at = models.DateField(
        "Fecha de inicio",
        null=True,
        default=None
    )

    is_current_center = models.BooleanField(
        "Marcar si este es el centro actual de la instancia",
        default=True,
        help_text=(
            "Indica sí la instancia actual es la empresa/centro donde se encuentra actualmente"
        )
    )

    rif = models.CharField(
        max_length=15,
        null=True,
        blank=True,
        default="",
        help_text=(
            "Ejemplo: J-1010101010"
        )
    )

    allow_clocking_from_another_workcenter = models.BooleanField(
        "Permitir chequeos de empleados de otra empresa",
        default=False
    )

    class Meta:
        verbose_name = "Empresa/Centro de trabajo"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.rif is not None and self.rif.strip() != "":
            if "J-" != self.rif[:1].upper():
                self.rif = f"J-{self.rif}"

        return super().save(*args, **kwargs)

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

    allow_qr_clocking = models.BooleanField(
        "Permitir chequeo por QR",
        default=True
    )

    allow_fingerprint_clocking = models.BooleanField(
        "Permitir chequeo por huella",
        default=False
    )
    
    allow_clocking_from_another_workcenter = models.BooleanField(
        "Permitir chequeos de empleados de otra empresa",
        default=False
    )

    work_center = models.ForeignKey(
        WorkCenter,
        on_delete=models.RESTRICT,
        related_name="entrypoints",
        null=True,
        default=None,
        verbose_name="Empresa"
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

    work_center = models.ForeignKey(
        WorkCenter, 
        on_delete=models.SET_NULL, 
        null=True, 
        default=None, 
        related_name="departments",
        verbose_name="Empresa"
    )
    objects = DepartmentManager.from_queryset(DepartmentQuerySet)()

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

    
    def __str__(self):
        return self.name
    

class Timetable(TimeStampedModel):
    department = models.ForeignKey(Department, on_delete=models.RESTRICT, related_name="timetables", verbose_name="Departamento")
    start_time = models.TimeField("Hora de inicio del turno")
    end_time = models.TimeField("Hora de salida del turno")
    is_active = models.BooleanField("Configuracion activa", default=True)

    
    class Meta:
        verbose_name = "Configuraciones de horario"
        verbose_name_plural = "Configuración horaria"


    def get_correct_time_range(self):
        """
        Para hacer un calculo de horas se necesita restar el tiempo final al tiempo inicial
        """
        
        if self.start_time > self.end_time:
            return self.end_time, self.start_time
        
        return self.start_time, self.end_time