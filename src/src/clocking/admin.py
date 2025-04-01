from typing import Any
from datetime import datetime, timedelta
from django.contrib import admin
from django.db.models.query import QuerySet
from django.db.models import Count, Q
from django.http.request import HttpRequest
from .models import DailyCalendar, DailyChecks, DailyCalendarObservation, DailyChecksProxyModelAdmin
from unfold.admin import ModelAdmin
from django.utils.html import format_html


# Register your models here.


class CheckingCalendarAdmin(admin.TabularInline):
    model = DailyChecks

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).order_by("-created").select_related(
            "employee", 
            "employee__position",
            "daily"
        )
    
    def get_readonly_fields(self, request: HttpRequest, obj):
        if obj:
            return ["employee", 'checking_time', 'checking_type']
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

    class Media:
        js = ('js/jquery.min.js', 'js/select2/select2.full.min.js', 'js/select2/select2_observations.js')   
        css = {
            'all': ('css/select2/select2.css',),
        }

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


class FilterByDateCalendar(admin.SimpleListFilter):
    title = "Buscar por fecha"
    parameter_name = "datelookup"
    template = "admin_filters/filter_calendar.html"

    def lookups(self, request, model_admin):
        hours_ago_24 = datetime.now() - timedelta(hours=24)
        return [
            (hours_ago_24.strftime("%Y-%m-%d"), "Ayer"),
            (datetime.now().strftime("%Y-%m-%d"), "Hoy"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "" or self.value() is None:
            return queryset
        return queryset.filter(daily__date_day=self.value())



@admin.register(DailyChecksProxyModelAdmin)
class DailyChecksModelAdmin(ModelAdmin):
    list_display = ["employee_name", "employee_last_name", "daily_day",  "checking_time", "checking_type"]
    search_fields = ['employee__name', "employee__last_name", "daily__date_day"]
    list_filter = ["checking_type", FilterByDateCalendar]
    list_per_page  = 15

    class Media:
        js = ('js/jquery.min.js', 'js/select2/select2.full.min.js', 'js/select2/start_select_clockin.js')   
        css = {
            'all': ('css/select2/select2.css',),
        }


    def get_queryset(self, request):
        return super().get_queryset(request).select_related("employee", "daily").order_by("-checking_time")
    
    def employee_name(self, obj):
        return obj.employee.name

    def employee_last_name(self, obj):
        return obj.employee.last_name
    
    def daily_day(self, obj):
        return obj.daily.date_day.strftime("%d/%m/%Y")
    
    employee_name.short_description = "Nombre"
    employee_last_name.short_description = "Apellido"
    daily_day.short_description = "Día"