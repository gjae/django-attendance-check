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
        .filter(
            Q(checking_time__date=yesterday.date()) 
            | Q(checking_time__date=today.date(), checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida)
        )
        .order_by("employee_id", "-id")
        .select_related("employee")
    )

    log.info(f"Reporte para la fecha {yesterday} - {today}: {checks}")
    for check in checks:
        if len(stack) == 0:
            stack.append(check)
        else:
            if stack[0].employee_id == check.employee_id:
                prev = stack.pop()
                total_hours = (check.checking_time - prev.checking_time ).total_seconds() / 60 / 60
                reports.append(
                    TimeReport(
                        employer_id=check.employee_id, 
                        total_hours=total_hours, 
                        created=yesterday,
                        end_at=check.checking_time,
                        start_at=prev.checking_time
                    )
                )


    if len(reports) > 0:
        TimeReport.objects.bulk_create(reports)