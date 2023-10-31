import pytest

from src.employees.models import Employee




pytestmark = pytest.mark.django_db


def test_employer_actived_default():
    e = Employee.objects.create(
        name="Test",
        last_name="Case",
        cedula=123456
    )


    assert e.status == Employee.STATUS.actived


def test_employer_doesnt_exitst():
    """
    Verificar que no se permite chequear a un empleado no registrado
    en base de datos
    """
    employer = Employee.objects.allow_checking(123456)

    assert not employer


def test_rejected_employer_can_check():
    """
    Trabajadores desactivados no pueden
    realizar chequeos
    """

    Employee.objects.create(
        name="Test",
        last_name="Case",
        cedula=123456,
        status=Employee.STATUS.rejected
    )


    assert not Employee.objects.allow_checking(123456)

def test_employer_can_check():
    Employee.objects.create(
        name="Test",
        last_name="Case",
        cedula=123456
    )

    assert Employee.objects.allow_checking(123456)