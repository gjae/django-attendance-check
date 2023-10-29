import logging
from config import celery_app

from src.clocking.models import DailyCalendar

@celery_app.task()
def create_current_date():
    """
    El único proposito de esta tarea es
    crear diariamente a las 12 de la noche el nuevo día del calendario
    """
    log = logging.getLogger(__name__)

    try:
        current_date = DailyCalendar.objects.get_or_create_clocking_day()
        log.info(f"Nuevo día en el calendario ha sido creado: f{current_date.date_day.strftime('%d/%m/%Y')}")
        return None
    except Exception as e:
        log.exception(e)
        return e
        