from datetime import datetime, date as date_cls
from django.urls import path
from django.contrib import admin
from django.utils.html import mark_safe
from unfold.admin import ModelAdmin
from django.contrib import messages
from django.contrib import admin


_admin_site_get_urls = admin.site.get_urls

# Register your models here.
from .models import (
    DiningChecking,
    ConfDiningRoom,
    GhostEmployee,
    GhostServiceLoad,
)
from .forms import ConfDiningRoomForm, GhostEmployeeForm, GhostServiceLoadForm
from src.reports.auditlog_admin import FriendlyLogEntryAdmin  # noqa: F401
from src.settings.models import WorkCenter
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
        # Empresas (WorkCenter) y procedencias (GhostEmployee) para el modal
        # de descarga de reportes (por empresa / por totalización)
        extra_context['work_centers'] = list(
            WorkCenter.objects.filter(is_removed=False).order_by("name")
            .values("id", "name")
        )
        extra_context['procedencias'] = list(
            GhostEmployee.objects.filter(is_removed=False)
            .order_by("name").values("id", "name")
        )
        extra_context['today_iso'] = datetime.now().date().isoformat()

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
            subrecords.delete()
        
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

@admin.register(GhostEmployee)
class GhostEmployeeModelAdmin(ModelAdmin):
    """
    Admin de comedor para crear y gestionar procedencias.

    Solo requiere un nombre para identificar su procedencia; no llevan un
    registro de asistencia asociado y no afectan los cálculos de asistencia
    del personal fijo. La relación opcional con Empresa (WorkCenter) hace
    que sus servicios cargados se sumen a la totalización del reporte por
    empresa, discriminados por tipo de beneficio. El flag interno
    is_removed (borrado lógico) no se muestra en el formulario.
    """

    form = GhostEmployeeForm
    list_display = ["id", "name", "empresa_name", "is_actived", "created"]
    search_fields = ["name"]
    list_filter = ["is_actived", "work_center"]
    exclude = ["is_removed"]

    @admin.display(description="Empresa", empty_value="General")
    def empresa_name(self, obj):
        """
        Muestra la empresa relacionada a la procedencia.

        Parámetros:
            obj (GhostEmployee): registro del listado.

        Retorna:
            str: nombre de la empresa o 'General' cuando la procedencia no
            tiene relación con ninguna empresa (solo aparece en el reporte
            general / totalización).
        """
        return obj.work_center.name if obj.work_center is not None else "General"

    def has_view_permission(self, request, obj=None):
        """
        Controla que solo usuarios con permiso de vista sobre Procedencias
        puedan acceder al listado y detalle.

        Parámetros:
            request (HttpRequest): petición actual.
            obj (GhostEmployee | None): registro puntual, si aplica.

        Retorna:
            bool: True si el usuario tiene el permiso correspondiente.
        """
        return request.user.has_perm("dining_room.view_ghostemployee")

    def has_add_permission(self, request):
        """
        Controla que solo usuarios con permiso de alta puedan crear
        Procedencias.

        Parámetros:
            request (HttpRequest): petición actual.

        Retorna:
            bool: True si el usuario tiene el permiso correspondiente.
        """
        return request.user.has_perm("dining_room.add_ghostemployee")

    def has_change_permission(self, request, obj=None):
        """
        Controla que solo usuarios con permiso de edición puedan modificar
        Procedencias.

        Parámetros:
            request (HttpRequest): petición actual.
            obj (GhostEmployee | None): registro puntual, si aplica.

        Retorna:
            bool: True si el usuario tiene el permiso correspondiente.
        """
        return request.user.has_perm("dining_room.change_ghostemployee")


@admin.register(GhostServiceLoad)
class GhostServiceLoadModelAdmin(ModelAdmin):
    """
    Admin de cocina para cargar la cantidad de servicios entregados a
    trabajadores fantasma por día y tipo de servicio.

    La primera carga de un día/tipo de servicio es la carga original; las
    siguientes se registran como erratas y SUMAN al total del día sin
    sobreescritura, permitiendo el control de beneficios fantasma sin afectar
    la asistencia del personal fijo.
    """

    list_display = [
        "id",
        "created",
        "day",
        "procedencia_name",
        "service_type_name",
        "quantity",
        "note",
        "loaded_by",
    ]
    list_filter = ["date_day", "service_type", "procedencia"]
    date_hierarchy = "date_day"

    form = GhostServiceLoadForm
    change_form_template = "unfold/dining/ghost_serviceload_change_form.html"

    def has_view_permission(self, request, obj=None):
        """
        Controla que solo usuarios con permiso de vista sobre Totalización de
        servicios puedan acceder al listado y detalle.

        Parámetros:
            request (HttpRequest): petición actual.
            obj (GhostServiceLoad | None): registro puntual, si aplica.

        Retorna:
            bool: True si el usuario tiene el permiso correspondiente.
        """
        return request.user.has_perm("dining_room.view_ghostserviceload")

    def has_add_permission(self, request):
        """
        Controla que solo usuarios con permiso de alta puedan registrar
        totalizaciones de servicios.

        Parámetros:
            request (HttpRequest): petición actual.

        Retorna:
            bool: True si el usuario tiene el permiso correspondiente.
        """
        return request.user.has_perm("dining_room.add_ghostserviceload")

    def has_change_permission(self, request, obj=None):
        """
        Controla que solo usuarios con permiso de edición puedan modificar
        totalizaciones de servicios.

        Parámetros:
            request (HttpRequest): petición actual.
            obj (GhostServiceLoad | None): registro puntual, si aplica.

        Retorna:
            bool: True si el usuario tiene el permiso correspondiente.
        """
        return request.user.has_perm("dining_room.change_ghostserviceload")

    def has_delete_permission(self, request, obj=None):
        """
        Habilita la opción "Eliminar" de Totalización de servicios únicamente
        para usuarios con el permiso dining_room.delete_ghostserviceload.

        La eliminación queda registrada en AUDITLOG automáticamente porque el
        modelo está registrado en django-auditlog (LogEntry de tipo delete),
        conservando el responsable vía AuditlogMiddleware.

        Parámetros:
            request (HttpRequest): petición actual.
            obj (GhostServiceLoad | None): registro puntual, si aplica.

        Retorna:
            bool: True si el usuario tiene permiso de eliminación.
        """
        return request.user.has_perm("dining_room.delete_ghostserviceload")

    def get_changeform_initial_data(self, request):
        """
        Precarga el día de hoy al abrir el formulario de totalización de
        servicios. El responsable de la carga no se precarga en el formulario
        porque se asigna automáticamente al usuario con sesión activa en
        save_model.

        Parámetros:
            request (HttpRequest): petición actual.

        Retorna:
            dict: datos iniciales del formulario.
        """
        return {"date_day": date_cls.today()}

    def save_model(self, request, obj, form, change):
        """
        Guarda la carga asignando automáticamente como responsable (loaded_by)
        al usuario con sesión activa y determinando el flag de errata cuando
        es una carga nueva (la primera del día/servicio/procedencia es
        original, el resto erratas).

        Parámetros:
            request (HttpRequest): petición actual.
            obj (GhostServiceLoad): instancia a guardar.
            form (ModelForm): formulario validado.
            change (bool): True si es edición de un registro existente.

        Retorna:
            None.
        """
        obj.loaded_by = request.user
        if not change:
            obj.is_errata = GhostServiceLoad.objects.actives().filter(
                date_day=obj.date_day,
                service_type=obj.service_type,
                procedencia=obj.procedencia,
            ).exists()

        super().save_model(request, obj, form, change)
        self.message_user(
            request,
            (
                f"Carga de {obj.quantity} servicios registrada para "
                f"{obj.service_type} el {obj.date_day.strftime('%d/%m/%Y')}"
            ),
            messages.SUCCESS,
        )

    @admin.display(description="Día")
    def day(self, obj):
        """
        Formatea el día de la carga en la lista del admin.

        Parámetros:
            obj (GhostServiceLoad): registro del listado.

        Retorna:
            str: fecha formateada dd/mm/aaaa.
        """
        return obj.date_day.strftime("%d/%m/%Y")

    @admin.display(description="Procedencia", empty_value="S/A")
    def procedencia_name(self, obj):
        """
        Muestra el nombre de la procedencia de la carga.

        Parámetros:
            obj (GhostServiceLoad): registro del listado.

        Retorna:
            str: nombre de la procedencia o 'S/A' si la carga no la tiene
            (cargas históricas creadas antes de la FK).
        """
        return str(obj.procedencia) if obj.procedencia is not None else "S/A"

    @admin.display(description="Tipo de servicio", empty_value="S/A")
    def service_type_name(self, obj):
        """
        Muestra el nombre del tipo de servicio de la carga.

        Parámetros:
            obj (GhostServiceLoad): registro del listado.

        Retorna:
            str: nombre del beneficio/servicio o 'S/A' si no está asociado.
        """
        return obj.service_type.check_name if obj.service_type is not None else "S/A"


def get_urls():
    urls = _admin_site_get_urls()
    urls = urls +  [
         path("dining_room/reports/", admin.site.admin_view(ReportAdminView.as_view()), name="dining_room.reports"),
    ]
    return urls

admin.site.get_urls = get_urls