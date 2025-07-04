from typing import Any
from datetime import datetime
from django.urls import reverse
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.http.response import HttpResponseRedirect
from django.utils.html import mark_safe
from unfold.admin import ModelAdmin
from django.contrib import messages
from django.utils.html import format_html
from unfold.admin import StackedInline, TabularInline

from src.clocking.models import DailyChecks
from .models import Employee, EmployeePosition, Transfer
from .forms import EmployerModelForm
from .models import Employee, EmployeePosition, Transfer, Department
from .forms import EmployerModelForm, TransferModelForm
from .models import Employee, EmployeePosition, Transfer, Department
from .forms import EmployerModelForm, TransferModelForm

@admin.action(description="Desactivar trabajador(es)")
def disable_employers(modeladmin, request, queryset):
    queryset.update(is_actived=False)
    modeladmin.message_user(
        request,
        "Los trabajadores seleccionados fueron correctamente desactivados",
        messages.SUCCESS,
    )

@admin.action(description="Activar trabajador(es)")
def active_employers(modeladmin, request, queryset):
    queryset.update(is_actived=True)
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
    
    employer: Employee = queryset.first()
    if employer.picture.name == '':
        modeladmin.message_user(
            request,
            f"El trabajador {employer.get_fullname()} no tiene cargada una foto, por lo que su carnet no puede ser generado",
            messages.ERROR
        )
        return False


    return HttpResponseRedirect(
        reverse("carnets.print", kwargs={"pk": queryset.first().id})
    )


@admin.action(description="Eliminar registro")
def delete_objects(modeladmin, request, queryset):
    updates = []
    for emp in queryset:
        emp.is_removed = True
        emp.deleted_at = datetime.now()
        emp.cedula = emp.id
        emp.save()

    modeladmin.message_user(
        request,
        "El/Los registros seleccionados fueron correctamente desactivados",
        messages.SUCCESS,
    )

    return True

class EmployerCheckingRecord(TabularInline):
    model = DailyChecks
    can_delete = False
    fields = ["fecha", "time", "checking_type"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).select_related(
            "employee", 
            "employee__position",
            "daily"
        )
    
    def get_readonly_fields(self, request: HttpRequest, obj):
        if obj:
            return ["fecha", 'time', 'checking_type', "daily"]
        else:  # When object is created
            return [] # no editable field
        
    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
    
    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

@admin.register(EmployeePosition)
class EmployeePositionAdmin(ModelAdmin):
    list_display = ["id", "created", "position", ]
    search_fields = ["position", ]

# Register your models here.
@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    search_fields = ["name", "last_name", "cedula"]
    list_per_page = 32
    inlines = [EmployerCheckingRecord, ]
    actions = [print_carnet, delete_objects, disable_employers, active_employers]
    form = EmployerModelForm
    list_filter = ["department", "position", ]

    fieldsets = (
        (
            "Información Personal", 
            {
                "fields": (
                    ("name", "last_name", "cedula", "birthday_at"),
                )
            }
        ),
        (
            "Ficha del Trabajador",
            {
                "fields": (
                    ("date_entry_job", "position"),
                    "department",
                    "picture",
                )
            }
        )
    )

    class Media:
        js = ('js/jquery.min.js', 'js/select2/select2.full.min.js', 'js/select2/start_select_employee.js')   
        css = {
            'all': ('css/select2/select2.css',),
        }


    def get_readonly_fields(self, request, q):
        if q is not None and q.department is not None:
            pass
            #return ["department", ]
        
        return super().get_readonly_fields(request, q)

    @admin.display(empty_value="Sin registro")
    def photo_tag(self, obj):
        if obj.picture is None:
            return ""
        try:
            return mark_safe(
                f"<div>"
                f'<img src="{obj.picture.url}" alt="{obj.name}_picture" class="w-10 h-10 rounded-full" loading="lazy" decoding="async">'
                f"</div>"
            )
        except:
            return mark_safe(
                f"<div>"
                f'<img src="/static/images/branding/logo_inpromaro_lit.png" alt="default" class="w-10 h-10 rounded-full" loading="lazy" decoding="async">'
                f"</div>"
            )
    
    @admin.display(empty_value="Sin registro")
    def last_checking(self, obj):
        last_check = obj.daily_checks.first()
        if last_check is None:
            return "Sin registros"
        
        return mark_safe(
            f'<div>'
            f'<span class="bg-blue-100 text-blue-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300">{last_check}</span>'
            f'</div>'
        )
    
    def delete_queryset(self, request, queryset):
        queryset.update(deleted_at=datetime.now())

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).select_related("position", "department", "department__work_center").prefetch_related("daily_checks", "daily_checks__daily")

    @admin.display(empty_value="S/A")
    def position_user(self, obj):
        return obj.position.position
    
    def get_inline_instances(self, request: HttpRequest, obj = None):
        if obj is not None:
            return super().get_inline_instances(request, obj)
        
        return []
    
    photo_tag.short_description = "Foto"
    position_user.short_description = "Cargo"
    last_checking.short_description = "Último chequeo"


    list_display = [
      "photo_tag",  "name", "last_name", "cedula", "department", "birthday_at", "position_user", "date_entry_job", "last_checking", "work_center", "actived"
    ]

    def has_delete_permission(self, request, obj=None):
        return False
    
    @admin.display(description="Empresa")
    def work_center(self, obj):
        if obj.department is not None and obj.department.work_center is not None:
            return obj.department.work_center.name

        return "S/A"

    def name(self, obj):
        return format_html(
            "<a href='/admin/employees/employee/{}/change/'>{}</a>",
            obj.id,
            obj.name
        )

    def actived(self, obj):
        if obj.is_actived:
            return "Actiado"

        return "Desactivado"

    name.short_description = "Nombre"
    actived.short_description = "Estado"


@admin.register(Transfer)
class TransferModelAdmin(ModelAdmin):
    model = Transfer
    form = TransferModelForm
    list_display = [
        "from_department",
        "to_department",
        "employee",
        "user",
        "note"
    ]
    fieldsets = (
        ("Origen y destino", {
            "fields": (
                "from_department",
                "to_department"
            ),
        }),
        ("Detalles", {
            "fields": (
                "employee",
                "note",
                "user"
            )
        })
    )
    
    exclude = ["is_removed", ]

    class Media:
        js = ('js/jquery.min.js', 'js/select2/select2.full.min.js', 'js/select2/start_select2.js')   
        css = {
            'all': ('css/select2/select2.css',),
        }

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related()
    def get_changeform_initial_data(self, request):
        return {"user": request.user.id, "from_department": Department.objects.first().id}
