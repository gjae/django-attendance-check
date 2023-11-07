from typing import Any
from django.urls import reverse
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponseRedirect
from django.utils.html import mark_safe
from unfold.admin import ModelAdmin
from django.contrib import messages

from src.clocking.models import DailyChecks
from .models import Employee, EmployeePosition
from .forms import EmployerModelForm

@admin.action(description="Generar e imprimir carnet")
def print_carnet(modeladmin, request, queryset):
    if queryset.count() > 1 or queryset.count() == 0:
        modeladmin.message_user(
            request,
            "Solo puede seleccionar un unico empleado a la vez para generar e imprimir su carnet",
            messages.ERROR,
        )

        return False
    

    return HttpResponseRedirect(
        reverse("carnets.print", kwargs={"pk": queryset.first().id})
    )


class EmployerCheckingRecord(admin.TabularInline):
    model = DailyChecks
    can_delete = False
    fields = ["fecha", "time", "checking_type"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).select_related(
            "employee", 
            "employee__position",
            "daily"
        )
    
    def get_readonly_fields(self, request: HttpRequest, obj):
        if obj:
            return ["fecha", 'time', 'checking_type', "daily"]
        else:  # When object is created
            return [] # no editable field
        
    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
    
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

@admin.register(EmployeePosition)
class EmployeePositionAdmin(ModelAdmin):
    list_display = ["id", "created", "position", ]
    search_fields = ["position", ]

# Register your models here.
@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    search_fields = ["name", "last_name", "cedula"]
    list_per_page = 32
    inlines = [EmployerCheckingRecord, ]
    actions = [print_carnet, ]
    form = EmployerModelForm

    fieldsets = (
        (
            "Información Personal", 
            {
                "fields": (
                    ("name", "last_name", "cedula"),
                )
            }
        ),
        (
            "Ficha del Trabajador",
            {
                "fields": (
                    ("date_entry_job", "position"),
                    "department",
                    "picture",

                )
            }
        )
    )


    @admin.display(empty_value="Sin registro")
    def photo_tag(self, obj):
        return mark_safe(
            f"<div>"
            f'<img src="{obj.picture.url}" alt="{obj.name}_picture" class="w-10 h-10 rounded-full" loading="lazy" decoding="async">'
            f"</div>"
        )
    
    @admin.display(empty_value="Sin registro")
    def last_checking(self, obj):
        last_check = obj.daily_checks.first()
        if last_check is None:
            return "Sin registros"
        
        return mark_safe(
            f'<div>'
            f'<span class="bg-blue-100 text-blue-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300">{last_check}</span>'
            f'</div>'
        )
    
    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).select_related("position", "department").prefetch_related("daily_checks", "daily_checks__daily")

    @admin.display(empty_value="S/A")
    def position_user(self, obj):
        return obj.position.position
    
    def get_inline_instances(self, request: HttpRequest, obj = None):
        if obj is not None:
            return super().get_inline_instances(request, obj)
        
        return []
    
    photo_tag.short_description = "Foto"
    position_user.short_description = "Cargo"
    last_checking.short_description = "Último chequeo"


    list_display = [
      "photo_tag",  "name", "last_name", "cedula", "position_user", "date_entry_job", "last_checking"
    ]
