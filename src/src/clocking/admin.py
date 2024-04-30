from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.db.models import Count, Q
from django.http.request import HttpRequest
from .models import DailyCalendar, DailyChecks, DailyCalendarObservation
from unfold.admin import ModelAdmin
from django.utils.html import format_html


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
    list_display = ["date_day", "checkings"]
    inlines = [CheckingCalendarAdmin, ]
    readonly_fields = ["date_day", ]

    def get_queryset(self, request: HttpRequest):
        return super().get_queryset(request).annotate(
            total_checkings=Count("daily_user_checks", distinct=True, filter=Q(daily_user_checks__checking_type=0))
        )


    def has_add_permission(self, request) -> bool:
        return False
    
    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
    
    def checkings(self, obj):
        return obj.total_checkings
    
    checkings.short_description = "Chequeos hasta el momento"

@admin.register(DailyCalendarObservation)
class DailyCalendarObservationAdmin(ModelAdmin):
    list_display = ["created", "calendar_day", "employer", "soporte"]
    list_filter = ["calendar_day", "employer", ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("calendar_day", "employer")

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
    
    def soporte(self, obj):
        if obj.support is None or obj.support.name is None or obj.support.name == "":
            return ""
        
        return format_html(
            "<a href='{}'><span class='material-symbols-outlined'>download</span></a>",
            obj.support.url,
        )
    
    soporte.short_description = "Soporte"