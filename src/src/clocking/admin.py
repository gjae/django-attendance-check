from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from .models import DailyCalendar, DailyChecks
from unfold.admin import ModelAdmin

# Register your models here.


class CheckingCalendarAdmin(admin.TabularInline):
    model = DailyChecks

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).select_related(
            "employee", 
            "employee__position",
            "daily"
        )
    
    def get_readonly_fields(self, request: HttpRequest, obj):
        if obj:
            return ["employee", 'time', 'checking_type']
        else:  # When object is created
            return [] # no editable field
    
@admin.register(DailyCalendar)
class DailyCalendarAdmin(ModelAdmin):
    list_display = ["date_day", ]
    inlines = [CheckingCalendarAdmin, ]
    readonly_fields = ["date_day", ]


    def has_add_permission(self, request) -> bool:
        return False
    
    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False