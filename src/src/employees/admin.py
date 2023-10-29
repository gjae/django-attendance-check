from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.utils.html import mark_safe

from .models import Employee, EmployeePosition

@admin.register(EmployeePosition)
class EmployeePositionAdmin(admin.ModelAdmin):
    list_display = ["id", "created", "position", ]
    search_fields = ["position", ]

# Register your models here.
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    search_fields = ["name", "last_name", "cedula"]
    list_per_page = 32

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
                    "picture",

                )
            }
        )
    )


    def photo_tag(self, obj):
        return mark_safe(
            f"<div>"
            f'<img src="{obj.picture.url}" alt="{obj.name}_picture" class="w-10 h-10 rounded-full" loading="lazy" decoding="async">'
            f"</div>"
        )
    
    def last_checking(self, obj):
        last_check = obj.daily_checks.first()
        return mark_safe(
            f'<div>'
            f'<span class="bg-blue-100 text-blue-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300">{last_check}</span>'
            f'</div>'
        )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).select_related("position").prefetch_related("daily_checks")

    @admin.display(empty_value="S/A")
    def position_user(self, obj):
        return obj.position.position
    
    photo_tag.short_description = "Foto"
    position_user.short_description = "Cargo"
    last_checking.short_description = "Último chequeo"


    list_display = [
      "photo_tag",  "name", "last_name", "cedula", "position_user", "date_entry_job", "last_checking"
    ]