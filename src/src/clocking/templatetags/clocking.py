from django import template
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from src.clocking.models import DailyCalendar, DailyChecks, DailyCalendarObservation, DailyChecksProxyModelAdmin
from src.employees.models import Employee, EmployeePosition


register = template.Library()

@register.simple_tag(takes_context=True)
def has_clocking_permissions(context):
    """
    Verifica que el usuario tenga permisos para ver los reportes de asistencia
    """
    if context["user"].is_superuser:
        return True

    content_type = [
        ContentType.objects.get_for_model(DailyCalendar),
        ContentType.objects.get_for_model(DailyChecks),
        ContentType.objects.get_for_model(DailyCalendarObservation),
        ContentType.objects.get_for_model(EmployeePosition),
        ContentType.objects.get_for_model(Employee),
    ]

    perms = context["user"].user_permissions.filter(content_type__in=content_type)
    if not perms.exists():
        groups = Group.objects.filter(user__id=context["user"].id).filter(permissions__content_type__in=content_type)
        return groups.exists()
    
    return perms.exists()


@register.simple_tag(takes_context=True)
def element_by_key(context , dictionary, key):
    return dictionary.get(key, [])