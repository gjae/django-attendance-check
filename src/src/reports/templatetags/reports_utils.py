from django import template

from src.reports.utils import has_observation
from src.utils.number import parse_float_to_time

register = template.Library()

@register.simple_tag(takes_context=True)
def day_has_observation(context, day, observations):
    return has_observation(day, observations)


@register.filter
def get_total_days_by_user(user, counters):
    if isinstance(user, dict):
        return counters[user["id"]]
    return counters[user.id]

@register.filter
def get_by_index(iterable, index):
    return iterable[index]

@register.filter
def parse_float_to_hours(value):
    return parse_float_to_time(value)
