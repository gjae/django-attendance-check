from datetime import datetime, timedelta
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
    
    now = datetime.now(instance.calendar_day.date_day.year, instance.calendar_day.date_day.month, instance.calendar_day.date_day.day, 8,0,0,0)
    end = now + timedelta(hours=8)

    if check_counter == 0 and instance.check_type == 3:
        DailyChecks.objects.create(
            employee=instance.employer,
            checking_type=0,
            time=now.time(),
            checking_time=now
        )
        DailyChecks.objects.create(
            employee=instance.employer,
            checking_type=1,
            time=end.time(),
            checking_time=now
        )

    elif check_counter == 1 and instance.check_type == 2:
        f = checks_by_user.first()
        end = f.checking_time + timedelta(hours=8)
        DailyChecks.objects.create(
            employee=instance.employer,
            checking_type=1,
            time=end.time(),
            checking_time=now
        )