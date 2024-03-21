from django.contrib import admin
from django.utils.html import mark_safe
from unfold.admin import ModelAdmin

# Register your models here.
from .models import DiningChecking



@admin.register(DiningChecking)
class DiningCheckingModelAdmin(ModelAdmin):
    list_display = ["id", "employer_name", "employer_last_name", "created", ]

    def get_queryset(self, request = None):
        return super().get_queryset(request).select_related(
            "employer",
            "conf_dining_room",
            "identity",
        )
    

    @admin.display(empty_value="Sin registro")
    def employer_name(self, obj):
        return obj.employer.name
    


    @admin.display(empty_value="Sin registro")
    def employer_last_name(self, obj):
        return obj.employer.last_name