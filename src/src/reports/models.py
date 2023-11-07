from django.db import models
from model_utils.models import TimeStampedModel

from src.employees.models import Employee

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
