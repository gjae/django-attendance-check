import pytest

from celery.result import EagerResult
from src.clocking.models import DailyCalendar
from src.clocking.tasks import create_current_date


pytestmark = pytest.mark.django_db


def test_create_an_only_canlerndar_day_per_day_using_manager(settings):
    """
    Comprueba que se crea solo un día de la misma fecha y no las duplique
    """
    
    settings.CELERY_TASK_ALWAYS_EAGER = True

    DailyCalendar.objects.get_or_create_clocking_day()
    DailyCalendar.objects.get_or_create_clocking_day()

    assert DailyCalendar.objects.count() == 1


def test_task_create_current_date(settings):
    """
    Comprueba la tarea create_current_date 
    """
    settings.CELERY_TASK_ALWAYS_EAGER = True

    task_result = create_current_date.delay()

    assert isinstance(task_result, EagerResult)
    assert task_result.result is None
    assert not isinstance(task_result.result, Exception)