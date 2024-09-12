from typing import Optional
from datetime import datetime
from django.db import models
from django.db.models import Q, Count

class EmployerNotPresentException(Exception):
    pass


class CheckDiningRoomManager(models.Manager):
    CURRENT_TIME_KEY = "current_time"

    def _get_current_time(self, **kwargs):
        CURRENT_TIME_KEY = self.CURRENT_TIME_KEY
        return kwargs.get(CURRENT_TIME_KEY, datetime.now().time())
    

    def get_current_checking_turn(self,  employer: models.Model, *args, **kwargs):
        from src.dining_room.models import ConfDiningRoom
        current_time = self._get_current_time(**kwargs)
        current_checking_turn = ConfDiningRoom.objects.filter(
            Q(start_time__lte=current_time)
            & Q(end_time__gte=current_time) 
            & Q(is_active__isnull=True)
            & Q(is_removed=False)
        ).first()

        return current_checking_turn
    
    def statistics_of(self, *, date = None):
        from src.clocking.models import DailyChecks
        if date is None:
            date = datetime.now()

        return DailyChecks.objects.filter(daily__date_day=date.date()).aggregate(
            assistants=Count(1, filter=Q(checking_type=DailyChecks.CHECK_STATUS_CHOISE.entrada)),
            retired=Count(1, filter=Q(checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida))
        )
    

    def can_empoloyer_check(self, employer: models.Model, *args, **kwargs):
        """"
        Verifica si un empleado puede realizar un chequeo en la hora y fecha actual.

        Retorna booleano True: puede hacer un chequeo, en caso de no poder se retornarà
        """
        current_checking_turn = self.get_current_checking_turn(employer, **kwargs)

        print(f"current_checking_turn 2 {current_checking_turn}")
        if current_checking_turn is None:
            return False
        
        # Verifica si el empleado no tiene un chqueo con el turno actual
        # entonces retorna que si puede hacer un chequeo
        has = not self.filter(employer=employer).filter(created__date=datetime.now().date()).filter(conf_dining_room=current_checking_turn).exists()

        print(f"HAS: {has}")
        return has

    def make_check_if_can(self, employer: models.Model, credential_card_id: Optional[int] = None, *args, **kwargs):
        """
        Hace un chequeo de parte del empleado 
        en caso de poder
        """
        from src.clocking.models import DailyChecks

        is_present = DailyChecks.objects.filter(employee_id=employer.id, daily__date_day=datetime.now().date()).count()
        current_checking_turn = self.get_current_checking_turn(employer)

        if is_present == 0 or is_present % 2 == 0:
            raise EmployerNotPresentException()
    

        if current_checking_turn is None or not self.can_empoloyer_check(employer):
            return None
        
        return self.create(
            conf_dining_room=current_checking_turn,
            identity_id=credential_card_id,
            employer=employer
        )
        

    def today_checks(self):
        return self.select_related("conf_dining_room", "employer").filter(created__date=datetime.now().date())