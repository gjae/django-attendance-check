from django import template

from src.reports.utils import has_observation

register = template.Library()

@register.simple_tag(takes_context=True)
def day_has_observation(context, day, observations):
    print(f"Dia: {day} / {observations}")
    return has_observation(day, observations)
