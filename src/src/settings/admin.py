from django.contrib import admin

from src.settings.models import ClientConfig
from src.settings.forms import ClientConfigModelForm


# Register your models here.
@admin.register(ClientConfig)
class ClientConfigAdminModel(admin.ModelAdmin):
    model = ClientConfig
    form = ClientConfigModelForm
    
    list_display = [
        "description", "created", "client_ip", "status"
    ]
    search_fields = ["description", "client_ip"],
    list_filter = ["status", ]
    list_per_page = 37

    fieldsets = (
        (
            "Equipo",
            {
                "fields": (
                    ("client_ip", "description")
                )
            }
        ),
        (
            "Observaciones",
            {
                "fields": (
                    "note", 
                )
            }
        )
    )
