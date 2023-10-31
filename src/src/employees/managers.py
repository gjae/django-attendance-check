import logging
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class EmployerManager(models.Manager):

    def allow_checking(self, cedula: int) -> bool:
        """
        Verifica si, dado un número de cédula, el trabajador puede marcar 
        entrada/salida. Retornará False a partir del momento en que el empleado
        comienza a estar dentro de los status que no permiten dicha acción
        """

        log = logging.getLogger(__name__)

        from src.employees.models import Employee

        employer = None
        try:
            employer = Employee.objects.get(cedula=cedula)
        except ObjectDoesNotExist:
            employer = None
            log.warning(f"Cédula {cedula} intetó marcar asistencia pero dicha cédula no fue encontrada en la base de datos")
            return False
        
        return employer.allow_checking