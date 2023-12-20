import logging
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from config import celery_app

from src.clocking.models import DailyChecks
from src.reports.models import TimeReport

@celery_app.task()
def hour_counter_task():
    """
    Diario a cierta hora del dia antes de comenzar la jornada,
    se inspecciona la Base de datos para generar un reporte del total de horas
    de cada usuario para ese día especifico
    """

    yesterday = timezone.now() - timedelta(days=1)
    today = timezone.now()
    stack = list()
    reports = []

    log = logging.getLogger(__name__)

    log.info("Iniciando reporte de contador de horas")

    checks = (
        DailyChecks
        .objects
        .report_by_employee(None, yesterday, yesterday, use_for_database=True)
    )

    log.info(f"Reporte para la fecha {yesterday} - {today}: {checks}")
    for check in checks:
        reports.append(
            TimeReport(
                employer_id=check["employer"].id, 
                total_hours=check["abs_total_hours"] * 1.0, 
                created=yesterday,
                end_at=check["start_at"],
                start_at=check["end_at"]
            )
        )


    if len(reports) > 0:
        TimeReport.objects.bulk_create(reports)