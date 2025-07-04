import logging
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class BaseCheckingManager(models.Manager):
    def get_model(self):
        from src.employees.models import Employee
        return Employee

    def get_identity_fieldname(self):
        return "cedula"

    def allow_checking(self, cedula: int) -> bool:
        """
        Verifica si, dado un número de cédula, el trabajador puede marcar 
        entrada/salida. Retornará False a partir del momento en que el empleado
        comienza a estar dentro de los status que no permiten dicha acción
        """

        log = logging.getLogger(__name__)
        Employee = self.get_model()

        employer = None
        try:
            search_by = {self.get_identity_fieldname(): cedula}
            employer = Employee.objects.get(**search_by)
        except ObjectDoesNotExist:
            employer = None
            log.warning(f"Cédula {cedula} intetó marcar asistencia pero dicha cédula no fue encontrada en la base de datos")
            return False
        
        return employer.allow_checking

class EmployerManager(BaseCheckingManager):

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def absences_between_dates(self, start_at, end_at):
        from src.clocking.models import DailyChecks


        return []


    def only_actives(self):
        from src.employees.models import Employee
        return self.exclude(status=Employee.STATUS.rejected)
    