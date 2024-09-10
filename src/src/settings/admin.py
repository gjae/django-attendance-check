import logging
from django.contrib import messages
from django.contrib import admin
from unfold.admin import ModelAdmin

from src.settings.models import ClientConfig,  Department, WorkCenter
from src.settings.forms import ClientConfigModelForm, WorkCenterCreateForm


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
class ClientConfigAdminModel(ModelAdmin):
    model = ClientConfig
    form = ClientConfigModelForm
    actions = [active_client_status, disable_client_status]
    
    list_display = [
        "description", "work_center", "created", "client_ip", "status"
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
            "Configuración",
            {"fields": (
                ("work_center", "allow_qr_clocking", "allow_clocking_from_another_workcenter")
            )}
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

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("work_center")
        return queryset

@admin.register(WorkCenter)
class WorkCenterModelAdmin(ModelAdmin):
    model = WorkCenter
    list_display = [
        "id",
        "created",
        "name",
        "code",
        "address",
        "is_active", 
        "main",
        "opened_at"
    ]
    form = WorkCenterCreateForm



@admin.register(Department)
class DepartmentModelAdmin(ModelAdmin):
    model = Department
    list_display = [
        "name",
        "work_center",
        "is_actived",
    ]

    fieldsets = (
        (None, {
            "fields": (
                "is_actived",
                "name",
                "work_center"
            ),
        }),
    )
    
    search_fields = ["name", "work_center"]
    list_filter = ["is_actived", "work_center"]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("work_center")

    def is_actived(self, obj):
        if obj.is_actived:
            return "Activo"
        
        return "Inactivo"
        
