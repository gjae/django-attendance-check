from django.dispatch import receiver
from django.db.models.signals import post_save

from src.clocking.models import DailyCalendarObservation, DailyChecks


@receiver(post_save, sender=DailyCalendarObservation)
def on_create_observation_save_checking(sender, instance: DailyCalendarObservation, created: bool, *args, **kwargs):
    if not created:
        return None
    
    checks_by_user = DailyChecks.objects.filter(daily=instance.calendar_day, employee=instance.employer)
    check_counter = checks_by_user.count()

    if check_counter == 2:
        return None
    
    if check_counter == 1 and DailyCalendarObservation.OBSERVATION_TYPE_CHOICES.checkin:
        return None
    

    return DailyChecks.objects.create()