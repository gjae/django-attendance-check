from uuid import uuid4
from datetime import datetime
from django.db import models
from django.conf import settings
from model_utils.models import TimeStampedModel
from model_utils import Choices
from model_utils.fields import StatusField
# Create your models here.

from src.employees.models import Employee
from .managers import ClockingManager, CheckingManager


class DailyCalendar(TimeStampedModel):
    date_day = models.DateField("Calendario de chequeos", db_index=True)

    objects = ClockingManager()

    class Meta:
        ordering = ["-date_day", ]
        verbose_name = "Calendario del sistema"
        verbose_name_plural = "Días del calendario"

    def __str__(self):
        return f"Registro del día {self.date_day.strftime('%d/%m/%Y')}"


class DailyChecks(TimeStampedModel):
    CHECK_STATUS_CHOISE = Choices((0, "entrada", "Entrada"), (1, "salida", "Salida"))
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="daily_checks", verbose_name="Trabajador")
    daily = models.ForeignKey(DailyCalendar, on_delete=models.CASCADE, related_name="daily_user_checks")

    time = models.TimeField("Hora de chequeo", auto_now_add=True)
    checking_time = models.DateTimeField("Fecha de chequeo", null=True, default=None)

    checking_type = models.IntegerField(
        "Tipo de chequeo",
        choices=CHECK_STATUS_CHOISE,
        default=CHECK_STATUS_CHOISE.entrada
    )


    objects = CheckingManager()


    class Meta:
        ordering = ["-daily__date_day", "employee_id", "-id"]
        verbose_name = "Chequeo del día"
        verbose_name_plural = "Chequeos diarios"


    def __str__(self):
        return f"{DailyChecks.CHECK_STATUS_CHOISE[self.checking_type]} - {self.daily.date_day.strftime('%d/%m/%Y')} {self.time.strftime('%H:%M')}"
    

    @property
    def fecha(self):
        return f"{self.daily.date_day.strftime('%d/%m/%Y')}"
        

    def save(self, *args, **kwargs):
        if self.checking_time is None:
            self.checking_time = datetime.now()
            
        return super().save(*args, **kwargs)
    

class DailyChecksProxyModelAdmin(DailyChecks):
    class Meta:
        ordering = ["-daily__date_day", "employee_id", "-id"]
        verbose_name = "Asignar chequeos"
        verbose_name_plural = "Asignar chequeos"
        proxy = True




class DailyCalendarObservation(TimeStampedModel):
    OBSERVATION_TYPE_CHOICES = Choices(
        # (1, "checkin", "Entrada"),
        (2, "checkout", "Salida"),
        (3, "checkin_out", "Entrada y salida")
    )

    calendar_day = models.ForeignKey(DailyCalendar, on_delete=models.CASCADE, related_name="observations", verbose_name="Día del calendario")
    employer = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="calendar_observations", verbose_name="Trabajador")
    description = models.TextField("Descripción")
    support = models.FileField("Soporte", upload_to="uploads/dailycalendarsupports/", null=True, default=None)
    check_type = models.PositiveSmallIntegerField("Tipo de observación", choices=OBSERVATION_TYPE_CHOICES, default=OBSERVATION_TYPE_CHOICES.checkin_out)

    class Meta:
        verbose_name = "Observación de chequeo"
        verbose_name_plural = "Observaciones de chequeos"

    def __str__(self):
        return f"{self.employer}; {self.calendar_day.date_day.strftime('%d/%m/%Y')}"