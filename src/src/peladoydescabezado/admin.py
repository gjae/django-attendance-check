from datetime import datetime
from django.utils.html import mark_safe
from django.db.models import Q
from django.contrib import admin
import logging
from django.contrib import messages
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils import timezone
from unfold.views import UnfoldModelAdminViewMixin
from django.views.generic import TemplateView
from django.urls import reverse
from django.http.response import HttpResponseRedirect
from django.contrib.admin.filters import SimpleListFilter

from .models import (
    Person, 
    Table, 
    TableProxyModel,
    Farm,
    Pool,
    Department,
    Weightness,
    Control, 
    BasketProduction,
    ReportProxyModel,
)
from src.peladoydescabezado.forms import (
    FarmModelForm,
    PersonalModelForm,
    WeightnessModelForm,
)

from src.peladoydescabezado.utils import get_current_turn
# Register your models here.

class LoadDateFilter(SimpleListFilter):
    parameter_name = "load_date"
    title = "Filtro por fecha"

    
    # hide from filter pane
    def has_output(self):
        return False

    # these two function below must be implemented for SimpleListFilter to work
    # (any implementation that doesn't affect queryset is fine)
    def lookups(self, request, model_admin):
        return (request.GET.get(self.parameter_name), ''),

    def queryset(self, request, queryset):
        return queryset
    
class LoadTurnFilter(SimpleListFilter):
    parameter_name = "load_turn"
    title = "Filtro por turno"

        
    # hide from filter pane
    def has_output(self):
        return False

    # these two function below must be implemented for SimpleListFilter to work
    # (any implementation that doesn't affect queryset is fine)
    def lookups(self, request, model_admin):
        return (request.GET.get(self.parameter_name), ''),

    def queryset(self, request, queryset):
        return queryset

@admin.action(description="Desactivar trabajador(es)")
def disable_employers(modeladmin, request, queryset):
    queryset.update(is_disabled=True)
    modeladmin.message_user(
        request,
        "Los trabajadores seleccionados fueron correctamente desactivados",
        messages.SUCCESS,
    )

@admin.action(description="Activar trabajador(es)")
def active_employers(modeladmin, request, queryset):
    queryset.update(is_disabled=False)
    modeladmin.message_user(
        request,
        "Los trabajadores seleccionados fueron correctamente activados",
        messages.SUCCESS,
    )


@admin.action(description="Generar e imprimir carnet")
def print_carnet(modeladmin, request, queryset):
    if queryset.count() > 1 or queryset.count() == 0:
        modeladmin.message_user(
            request,
            "Solo puede seleccionar un unico empleado a la vez para generar e imprimir su carnet",
            messages.ERROR,
        )

        return False
    
    employer: Person = queryset.first()
    if employer.picture.name == '':
        modeladmin.message_user(
            request,
            f"El trabajador {employer.get_fullname()} no tiene cargada una foto, por lo que su carnet no puede ser generado",
            messages.ERROR
        )
        return False


    return HttpResponseRedirect(
        reverse("carnets.p.print", kwargs={"pk": queryset.first().id})+"?src=pelado"
    )


@admin.action(description="Desactivar mesas")
def disable_tables(modeladmin, request, queryset):
    queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        "Las mesas seleccionadas fueron desactivadas correctamente",
        messages.SUCCESS
    )


@admin.action(description="Activar mesas")
def enable_tables(modeladmin, request, queryset):
    queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        "Las mesas seleccionadas fueron activadas correctamente",
        messages.SUCCESS
    )


@admin.action(description="Archivar mesas")
def archive_tables(modeladmin, request, queryset):
    queryset.update(archived_at=timezone.now())
    modeladmin.message_user(
        request,
        "Las mesas seleccionadas fueron archivadas correctamente",
        messages.SUCCESS
    )

@admin.register(Weightness)
class WeightnessModelAdmin(ModelAdmin):
    list_display = [
        "created",
        "weight"
    ]
    form = WeightnessModelForm

@admin.register(Person)
class PeopleModelAdmin(ModelAdmin):
    search_fields = ["names", "lastnames", "identity", ]
    list_display = [
       "personal_photo", "identity", "names", "lastnames",  "department", "position", "created",  "state",
    ]
    form = PersonalModelForm
    fieldsets = (
        ("Datos Personales", {
            "fields": (
                ("names", "lastnames", "identity"),
            ),
        }),
        ("Identificación", {
            "fields": (
                ( "personal_pic", ),
            ),
        }),
        ("Datos Laborales", {
            "fields": (
                ("department", "position", ), 
            )
        })
    )
    actions = [print_carnet, active_employers, disable_employers]

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("department", "position")

    def state(self, obj):
        if obj.is_actived:
            return "Activo"
        
        return "Inactivo"

    def personal_photo(self, obj):
        if obj.personal_pic is None:
            return ""
        try:
            return mark_safe(
                f"<div>"
                f'<img src="{obj.personal_pic.url}" alt="{obj.names}_picture" style="max-width: 30px; max-heigh: 30px;" class="w-10 h-10 rounded-full" loading="lazy" decoding="async">'
                f"</div>"
            )
        except Exception as e:
            return mark_safe(
                f"<div>"
                f'<img src="/static/images/branding/logo_inpromaro_lit.png" style="max-width: 30px; max-heigh: 30px;" alt="default" class="w-10 h-10 rounded-full" loading="lazy" decoding="async">'
                f"</div>"
            )
        
    personal_photo.short_description = "Foto"
    state.short_description = "Estado"
    

@admin.register(Table)
class TableModelAdmin(ModelAdmin):
    list_display = [
       "id", "created", "description", "category", "is_active"
    ]

    list_filter = ["is_active", "category"]
    list_per_page = 18
    actions = [disable_tables, enable_tables, archive_tables]

    fieldsets = (
        (None, {
            "fields": (
                "is_active", 
            )
        }),
        
        (None, {
            "fields": (
                "description",
                "category",
            ),
        }),
    )
    

    def get_queryset(self, request):
        return super().get_queryset(request).filter(archived_at__isnull=True)
    



@admin.register(TableProxyModel)
class TableProxyModelAdmin(ModelAdmin):
    change_list_template = "unfold/peladoydescabezado/management.html"
    list_filter  = (
        LoadDateFilter,
        LoadTurnFilter
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        request.GET = request.GET.copy()
        self.custom_turn = request.GET.get("load_turn")
        self.custom_date = request.GET.get("load_date")
        print(request.GET)
        return queryset

    def changelist_view(self, request, extra_context=None):
        request.GET._mutable=True
        turns = {"morning": "Diurno", "night": "Nocturno", "evening": "Vespertino"}
        turns_id = {"morning": 0, "night": 1, "evening": 2}
        current_user = request.user
        show_date = request.GET.get("load_date", datetime.now().date())
        show_turn = int(request.GET.get("load_turn", turns_id[get_current_turn()]))

        if isinstance(show_date, str):
            show_date = datetime.strptime(show_date, "%Y-%m-%d")

        current_control_turn = Control.objects.control_by_turn(request.user, load_turn=show_turn, load_date=show_date)
        current_turn_production = []
        details = current_control_turn.details.prefetch_related("weightness").select_related("farm", "pool").all()
        current_details = [{
            "farm": detail.farm_id,
            "pool": detail.pool_id,
            "weights": [{"weight": w.id } for w in detail.weightness.all()],
            "total_weight": detail.total_weight_received
        } for detail in details]

        tables = []
        reverse_resolve_tables = {}
        for t in Table.objects.filter(is_active=True):
            tables.append({"id": t.id, "description": t.description})
            reverse_resolve_tables[t.id] = t.description

        for c in BasketProduction.objects.select_related("worker", "table").filter(control__turn=show_turn, control__date_upload=show_date, saved_by=request.user):
            current_turn_production.append({
                "id": c.id,
                "cedula": c.worker.identity,
                "fullname": str(c.worker),
                "weight": float(c.weight),
                "table": c.table.description,
                "date": c.created.strftime("%d/%m/%Y")
            })
        

        extra_context = {
            "farms": Farm.objects.get_farms_with_pool_as_dict(),
            "weightness": Weightness.objects.all(),
            "tables": tables,
            "reverse_resolve_tables": reverse_resolve_tables,
            "current_turn": int(show_turn),
            "current_turn_key": get_current_turn(show_turn),
            "current_control": Control.objects.control_by_turn(request.user, load_turn=show_turn, load_date=show_date),
            "control": current_control_turn,
            "progress": current_details,
            "turns_id": turns_id[get_current_turn(load_turn=show_turn)],
            "current_control_turn": current_turn_production,
            "current_user": current_user,
            "current_date": show_date,
        }

        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Farm)
class FarmModelAdmin(ModelAdmin):
    model = Farm
    list_display = [
        "name",
    ]
    form = FarmModelForm
    


@admin.register(Pool)
class PoolModelAdmin(ModelAdmin):
    model = Pool
    list_display = [
        "number",
        "farm"
    ]


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
    
    search_fields = ["name", ]
    list_filter = ["is_actived", "work_center"]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("work_center")


    def is_actived(self, obj):
        if obj.is_actived:
            return "Activo"
        
        return "Inactivo"
    

@admin.register(ReportProxyModel)
class RegisterModelAdmin(ModelAdmin):
    change_list_template = "unfold/peladoydescabezado/reports.html"

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            "departments": Department.objects.all(),
            "persons": Person.objects.exclude(is_disabled=False)
        }
        return super().changelist_view(request, extra_context=extra_context)