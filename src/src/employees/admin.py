from django.contrib import admin
from django.utils.html import mark_safe

from .models import Employee

# Register your models here.
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    search_fields = ["name", "last_name", "cedula"]

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
                    "date_entry_job",
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
    
    photo_tag.short_description = "Foto"


    list_display = [
      "photo_tag",  "name", "last_name", "cedula", "date_entry_job"
    ]