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


class CheckingManager(models.Manager):

    def checking_user(self, employee):
        """
        Realiza un check para el usuario para el día actual. Si el usuario
        tiene una entrada en el día actual entonces solo marca una salida

        Por día de calendario solo se puede tener máximo una entrada y una salida

        si el día anterior no tuvo salida y/o entrada, igual será marcado el día 
        actual e ignorará el anterior
        """

        from src.clocking.models import DailyCalendar, DailyChecks
        
        daily = DailyCalendar.objects.get_or_create_clocking_day()
        
        employee_calendar = DailyChecks.objects.filter(employee=employee, daily=daily)

        if not employee_calendar.exists():
            return DailyChecks.objects.create(employee=employee, daily=daily)
        
        elif employee_calendar.exists() and employee_calendar.first().checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada:
            return DailyChecks.objects.create(employee=employee, daily=daily, checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida)


        return None