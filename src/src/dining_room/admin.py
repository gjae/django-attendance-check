from datetime import datetime
from django.urls import path
from django.contrib import admin
from django.utils.html import mark_safe
from unfold.admin import ModelAdmin
from django.contrib import messages
from django.contrib import admin


_admin_site_get_urls = admin.site.get_urls

# Register your models here.
from .models import DiningChecking, ConfDiningRoom
from .forms import ConfDiningRoomForm
from .views import ReportAdminView


class DiningRoomProxyModel(ConfDiningRoom):
    class Meta:
        proxy = True
        verbose_name = "Gestión"
        verbose_name_plural = "Gestión de comedor"
        

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

@admin.register(DiningRoomProxyModel)
class ConfDiningRoomReportModelView(ModelAdmin):
    change_list_template = "unfold/dining/management.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = {}
        extra_context['today_statistics'] = DiningChecking.objects.statistics_of()
        extra_context['today_statistics']["presents"] = extra_context['today_statistics']["assistants"] - extra_context['today_statistics']["retired"]

        return super().changelist_view(request, extra_context=extra_context)

@admin.register(ConfDiningRoom)
class ConfDiningRoomModelAdmin(ModelAdmin):
    list_display = ["id", "created", "check_name", "start_time", "end_time", "actived"]
    actions = [action_disabled_turn, action_denable_turn, "remove_configuration"]
    form = ConfDiningRoomForm

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_removed=False)

    def actived(self, obj):
        if obj.is_active is None:
            return "Si"
        
        return "No"
    
    def has_delete_permission(self, *args, **kwargs):
        return False
    
    @admin.action(description="Eliminar registros seleccionados")
    def remove_configuration(self, request, queryset):
        for record in queryset:
            subrecords = record.checkings.all()
            subrecords.update(is_removed=True)
        
        queryset.update(is_removed=True)
        self.message_user(
            request,
            "Los registros seleccionados fueron correctamente removidos",
            messages.SUCCESS,
        )
    
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


class ReportModelAdmin(ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()

        return urls + [
            path("dining_room/reports/", ReportAdminView.as_view(model_admin=self), name="dining_room.reports"),
        ]

def get_urls():        
    urls = _admin_site_get_urls()
    urls = urls +  [
         path("dining_room/reports/", admin.site.admin_view(ReportAdminView.as_view()), name="dining_room.reports"),
    ]
    return urls

admin.site.get_urls = get_urls