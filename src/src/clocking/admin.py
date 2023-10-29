from django.contrib import admin
from .models import DailyCalendar

# Register your models here.


@admin.register(DailyCalendar)
class DailyCalendarAdmin(admin.ModelAdmin):
    list_display = ["date_day", ]
    