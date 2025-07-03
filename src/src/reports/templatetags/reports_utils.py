from django import template

from src.reports.utils import has_observation

register = template.Library()

@register.simple_tag(takes_context=True)
def day_has_observation(context, day, observations):
    return has_observation(day, observations)


@register.filter
def get_total_days_by_user(user, counters):
    return counters[user.id]

@register.filter
def get_by_index(iterable, index):
    return iterable[index]