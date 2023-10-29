from django.utils import timezone
from django.db import models



class ClockingManager(models.Manager):

    def get_or_create_clocking_day(self):
        """
        Verifica que la fecha actual ha sido registrada en el calendario del sistema
        para realizar los checkeos, si la fecha actual no ha sido registrada, será registrada
        y se retornara la referencia
        """
        
        today = timezone.now()
        current_date, _ = self.get_or_create(date_day=today.date())

        return current_date


