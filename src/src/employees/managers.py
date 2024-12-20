import logging
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class EmployerManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

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

    def absences_between_dates(self, start_at, end_at):
        from src.clocking.models import DailyChecks


        return []


    def only_actives(self):
        from src.employees.models import Employee
        return self.exclude(status=Employee.STATUS.rejected)
    