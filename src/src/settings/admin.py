import logging
from django.contrib import messages
from django.contrib import admin

from src.settings.models import ClientConfig
from src.settings.forms import ClientConfigModelForm


@admin.action(description="Activar cliente")
def active_client_status(modeladmin, request, queryset):
    """
    Activar cliente nuevamente
    """
    log = logging.getLogger(__name__)
    queryset.update(status=ClientConfig.STATUS.enabled)

    log.info("Los clientes seleccionados han sido correctamente activados")
    modeladmin.message_user(
        request,
        "El o los clientes seleccionados fueron correctamente reactivados",
        messages.SUCCESS,
    )



@admin.action(description="Desactivar cliente")
def disable_client_status(modeladmin, request, queryset):
    """
    Activar cliente nuevamente
    """
    log = logging.getLogger(__name__)
    queryset.update(status=ClientConfig.STATUS.disabled)

    log.info("Los clientes seleccionados han sido correctamente desactivados")
    modeladmin.message_user(
        request,
        "El o los clientes seleccionados fueron correctamente desactivados",
        messages.SUCCESS,
    )



# Register your models here.
@admin.register(ClientConfig)
class ClientConfigAdminModel(admin.ModelAdmin):
    model = ClientConfig
    form = ClientConfigModelForm
    actions = [active_client_status, disable_client_status]
    
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
