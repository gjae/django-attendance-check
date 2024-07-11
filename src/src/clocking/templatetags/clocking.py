from django import template
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from src.clocking.models import DailyCalendar, DailyChecks, DailyCalendarObservation, DailyChecksProxyModelAdmin


register = template.Library()

@register.simple_tag(takes_context=True)
def has_clocking_permissions(context):
    """
    Verifica que el usuario tenga permisos para ver los reportes de asistencia
    """
    content_type = [
        ContentType.objects.get_for_model(DailyCalendar),
        ContentType.objects.get_for_model(DailyChecks),
        ContentType.objects.get_for_model(DailyCalendarObservation),
    ]

    perms = context["user"].user_permissions.filter(content_type__in=content_type)
    return perms.exists()