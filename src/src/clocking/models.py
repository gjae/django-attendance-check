from django.db import models
from model_utils.models import TimeStampedModel
from model_utils import Choices
from model_utils.fields import StatusField
# Create your models here.

from src.employees.models import Employee
from .managers import ClockingManager, CheckingManager


class DailyCalendar(TimeStampedModel):
    date_day = models.DateField("Calendario de checkeos", db_index=True)

    objects = ClockingManager()

    class Meta:
        ordering = ["-date_day", ]
        verbose_name = "Calendario del sistema"
        verbose_name_plural = "Días del calendario"

    def __str__(self):
        return f"Registro del día {self.date_day.strftime('%d/%m/%Y')}"


class DailyChecks(TimeStampedModel):
    CHECK_STATUS_CHOISE = Choices((0, "entrada", "Entrada"), (1, "salida", "Salida"))
    employee = models.ForeignKey(Employee, on_delete=models.RESTRICT, related_name="daily_checks", verbose_name="Trabajador")
    daily = models.ForeignKey(DailyCalendar, on_delete=models.RESTRICT, related_name="daily_user_checks")

    time = models.TimeField("Hora de chequeo", auto_now_add=True)
    checking_time = models.DateTimeField("Fecha de checkeo", auto_now_add=True)

    checking_type = models.IntegerField(
        "Tipo de checqueo",
        choices=CHECK_STATUS_CHOISE,
        default=CHECK_STATUS_CHOISE.entrada
    )


    objects = CheckingManager()


    class Meta:
        ordering = ["-checking_time", "employee_id", "-id"]
        verbose_name = "Chequeo del día"
        verbose_name_plural = "Chequeos diarios"


    def __str__(self):
        return f"{DailyChecks.CHECK_STATUS_CHOISE[self.checking_type]} - {self.daily.date_day.strftime('%d/%m/%Y')} {self.time.strftime('%H:%M')}"
    

    @property
    def fecha(self):
        return f"{self.daily.date_day.strftime('%d/%m/%Y')}"