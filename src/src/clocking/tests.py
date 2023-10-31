import pytest

from celery.result import EagerResult
from src.clocking.models import DailyCalendar, DailyChecks
from src.clocking.tasks import create_current_date
from src.employees.models import Employee


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


def test_checking_employee_should_be_twice_daily():
    """
    Verifica que un trabajador solo pueda tener dos checkeos maximos
    por dia, uno de entrada y otro de salida unicamente
    """

    employer = Employee.objects.create(name="Test person")

    response = DailyChecks.objects.checking_user(employer)
    DailyChecks.objects.checking_user(employer)
    DailyChecks.objects.checking_user(employer)

    employer_checks = DailyChecks.objects.filter(employee=employer)

    assert employer_checks.count() == 2
    assert employer_checks.first().checking_type == DailyChecks.CHECK_STATUS_CHOISE.salida
    assert response.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada
    assert employer_checks.first().checking_time is not None
