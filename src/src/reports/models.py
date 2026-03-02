from django.db import models
from model_utils.models import TimeStampedModel
from model_utils import Choices
from django.contrib.auth import get_user_model

from src.employees.models import Employee
from src.reports.managers import TimeReportManager

User = get_user_model()

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


class ReportLog(TimeStampedModel):
    FORMATS = Choices(
        (0, "pdf", "PDF"),
        (1, "xlsx", "Excel"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_logs",
        verbose_name="Usuario"
    )

    report_name = models.CharField(
        "Nombre del reporte",
        max_length=200
    )

    report_format = models.SmallIntegerField(
        "Formato",
        choices=FORMATS
    )

    parameters = models.JSONField(
        "Parámetros",
        default=dict,
        blank=True
    )

    ip_address = models.GenericIPAddressField(
        "Dirección IP",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Log de reporte"
        verbose_name_plural = "Logs de reportes"
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user} - {self.report_name} ({self.get_report_format_display()})"