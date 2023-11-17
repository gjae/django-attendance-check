from django.db import models
from model_utils.models import TimeStampedModel

from src.employees.models import Employee
from src.reports.managers import TimeReportManager

# Create your models here.
class TimeReport(TimeStampedModel):
    employer = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    total_hours = models.DecimalField(
        "Cantidad de horas realizadas",
        default=0.00,
        max_digits=17,
        decimal_places=2
    )

    start_at = models.DateTimeField(
        "Hora de entrada",
        null=True,
        default=None
    )

    end_at = models.DateTimeField(
        "Hora de salida",
        null=True,
        default=None
    )

    objects = TimeReportManager()


    @property
    def abs_total_hours(self):
        return abs(self.total_hours)