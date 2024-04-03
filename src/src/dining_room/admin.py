from datetime import datetime
from django.contrib import admin
from django.utils.html import mark_safe
from unfold.admin import ModelAdmin
from django.contrib import messages

# Register your models here.
from .models import DiningChecking, ConfDiningRoom
from .forms import ConfDiningRoomForm

@admin.action(description="Desactivar Turno")
def action_disabled_turn(modeladmin, request, queryset):
    queryset.update(is_active=datetime.now())
    modeladmin.message_user(
        request,
        "El o los turnos seleccionados fueron correctamente desactivados",
        messages.SUCCESS,
    )


@admin.action(description="Reactivar Turno")
def action_denable_turn(modeladmin, request, queryset):
    queryset.update(is_active=None)
    modeladmin.message_user(
        request,
        "El o los turnos seleccionados fueron correctamente reactivados",
        messages.SUCCESS,
    )


@admin.register(ConfDiningRoom)
class ConfDiningRoomModelAdmin(ModelAdmin):
    list_display = ["id", "created", "check_name", "start_time", "end_time", "actived"]
    actions = [action_disabled_turn, action_denable_turn]
    form = ConfDiningRoomForm


    def actived(self, obj):
        if obj.is_active is None:
            return "Si"
        
        return "No"
    
    actived.short_description = "Turno activo"

@admin.register(DiningChecking)
class DiningCheckingModelAdmin(ModelAdmin):
    list_display = ["id", "employer_name", "employer_last_name", "created", "turno"]
    list_filter = ["conf_dining_room" ]

    def get_queryset(self, request = None):
        return super().get_queryset(request).filter(created__date=datetime.now().date()).select_related(
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
    
    @admin.display(empty_value="Sin registro")
    def turno(sekf, obj):
        return obj.conf_dining_room.check_name
    
    
    def has_add_permission(self, request) -> bool:
        return False
    
    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
    

    employer_last_name.short_description = "Apellido"
    employer_name.short_description = "Nombre"