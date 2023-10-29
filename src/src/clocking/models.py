from django.db import models
from django.contrib.auth import get_user_model
from model_utils.models import TimeStampedModel
# Create your models here.

from src.employees.models import Employee


class DailyCalendar(TimeStampedModel):
    date_day = models.DateField("Calendario de checkeos", db_index=True)


class DailyChecks(TimeStampedModel):
    employee = models.ForeignKey(Employee, on_delete=models.RESTRICT, related_name="daily_checks")
    daily = models.ForeignKey(DailyCalendar, on_delete=models.RESTRICT, related_name="daily_user_checks")