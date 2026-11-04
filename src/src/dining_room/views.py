from django.shortcuts import render
from datetime import datetime
import time
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.contrib.staticfiles import finders
from django.forms.models import model_to_dict
from django.views.generic import TemplateView
from django.http.response import HttpResponse
from django.db.models import Sum, Window, Q, Count
from django.db.models.functions import RowNumber

from src.dining_room.models import DiningChecking, ConfDiningRoom
from src.dining_room.models import GhostServiceLoad
from src.dining_room.reportering import ExcelReportBuilder
from src.settings.models import WorkCenter
from src.employees.models import Employee
from src.clocking.models import DailyChecks
from src.dining_room.managers import EmployerNotPresentException, EmployerHasBeenCheckedException
from src.peladoydescabezado.models import Person
from src.reports.audit import log_report
from unfold.views import UnfoldModelAdminViewMixin

# Create your views here.

class ReportAdminView(UnfoldModelAdminViewMixin, TemplateView):
    title = "Gestion de reportes de comedor"  # required: custom page header title
    permissions_required = (
        "dining_room.view_dining_room",
    ) # required: tuple of permissions
    template_name = "dining_room/report_admin_template.html"


@login_required
@permission_required("dining_room.view_conf_diningroom", raise_exception=True)
def report_dining_today_excel(request, *args, **kwargs):
    """
    Handler del builder de reportes de comedor (dining_room.reportering).

    Genera el reporte según los parámetros de la descarga hecha desde el
    modal de gestión de comedor (DiningRoomProxyModel):

    - report_type: 'empresa' (default) o 'totalizacion'.
    - print_date: fecha única (compatibilidad con el enlace anterior).
    - start_date / end_date: rango de fechas (end_date inclusive).
    - work_center: id de empresa o 'all' (solo reporte por empresa).
    - procedencia: id de GhostEmployee o 'all' (solo reporte por
      totalización; las cargas no están asociadas a una procedencia, por
      tanto la sección muestra los totales globales del rango).

    Requiere sesión activa y el permiso dining_room.view_conf_diningroom.
    Los "servicios entregados a procedencias" (GhostServiceLoad, cargas
    originales y erratas, estas últimas suman) se agregan al total por
    beneficio sin afectar los cálculos de asistencia del personal fijo.

    Parámetros:
        request (HttpRequest): petición con los filtros de reporte.

    Retorna:
        HttpResponse: archivo Excel (o tabla HTML en salida display)
        auditado con log_report.
    """
    filters = parse_report_filters(request.GET)

    builder = ExcelReportBuilder().enable_header()

    datasets = (
        totalization_services_dataset(filters)
        if filters["report_type"] == "totalizacion"
        else company_checks_dataset(filters)
    )

    for dataset in datasets:
        builder.add_dataset(dataset["rows"], dataset["layout"])

    response = builder.build()
    log_report(
        request,
        (
            "Reporte totalización de servicios de comedor"
            if filters["report_type"] == "totalizacion"
            else "Reporte comedor por empresa"
        ),
        "xlsx",
        {
            "report_type": filters["report_type"],
            "start_date": str(filters["start_date"]),
            "end_date": str(filters["end_date"]),
            "work_center": str(filters["work_center"]),
            "procedencia": str(filters["procedencia"]),
        },
    )
    return response


def index(request, *args, **kwargs):
    current_date = datetime.now().date()
    current_time = datetime.now().time()
    current_turn = ConfDiningRoom.objects.filter(date_start__date__lte=current_date, is_active__isnull=True, start_time__lte=current_time, end_time__gte=current_time).last()
    today_checks = DiningChecking.objects.today_checks(current_turn=current_turn)
    context = {}
    context['today_statistics'] = DiningChecking.objects.statistics_of()
    context['today_statistics']["presents"] = context['today_statistics']["assistants"] - context['today_statistics']["retired"]

    print(f"current_turn: {current_turn}")
    return render(
        request,
        "dining_room/index.html",
        {"today_checks": today_checks,
        "statistics": context['today_statistics'],
        "current_turn": current_turn,
        "total_checks": today_checks.filter(conf_dining_room=current_turn).count()}
    )

def default_today_last_checks(request, *args, **kwargs):
    today_checks = DiningChecking.objects.today_checks().order_by("-created")[0:39]
    response = []
    for check in today_checks:
        response.append({
            "name": check.employer.name,
            "lastname": check.employer.last_name,
            "position": check.employer.position.position if check.employer.position is not None else '',
            "department": check.employer.department.name if check.employer.department is not None else '',
            "id": check.employer.id,
            "avatar": check.employer.picture.url if check.employer is not None and check.employer.picture.name else '',
            "is_birthday": check.employer.is_birthday,
            "check_turn": check.conf_dining_room.check_name,
            "check_at": check.created.strftime("%I:%M %p")
        })

    return JsonResponse({
        "error": False,
        "data": response
    })


def parse_report_filters(query):
    """
    Traduce los parámetros GET del modal de reportes a un diccionario de
    filtros normalizado para el builder de reportes de comedor.

    Parámetros:
        query (QueryDict): parámetros GET de la petición.

    Retorna:
        dict: filtros normalizados:
            report_type (str): 'empresa' | 'totalizacion'.
            start_date (date), end_date (date): rango solicitado
            (print_date único se mapea al rango).
            work_center (int | 'all'): empresa seleccionada.
            procedencia (int | 'all'): procedencia seleccionada
            (solo usado como etiqueta en totalización).
    """
    today = datetime.now().date()

    start_date = query.get("start_date")
    end_date = query.get("end_date")
    print_date = query.get("print_date")

    if print_date and not start_date and not end_date:
        start_date = end_date = print_date

    def to_date(value, fallback):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return fallback

    start_date = to_date(start_date, today)
    end_date = to_date(end_date, start_date)

    work_center = query.get("work_center", "all")
    if work_center != "all":
        try:
            work_center = int(work_center)
        except (TypeError, ValueError):
            work_center = "all"

    procedencia = query.get("procedencia", "all")
    if procedencia != "all":
        try:
            procedencia = int(procedencia)
        except (TypeError, ValueError):
            procedencia = "all"

    return {
        "report_type": "totalizacion" if query.get("report_type") == "totalizacion" else "empresa",
        "start_date": start_date,
        "end_date": end_date,
        "work_center": work_center,
        "procedencia": procedencia,
    }


def company_checks_dataset(filters):
    """
    Arma el dataset del reporte "por empresa" replicando el layout del
    reporte original de comedor (7 columnas A-G, header A1:G1 en una fila,
    fila de encabezado fusionada con solo "Trabajador", nombre fusionado
    C:D por fila y bloque "Beneficio / Total/Día" sin negritas), con los
    cambios nuevos: rango de fechas y una hoja por empresa (WorkCenter).
    Los servicios de procedencias NO se mezclan aquí: corresponden
    exclusivamente al reporte por totalización.

    Parámetros:
        filters (dict): filtros de parse_report_filters.

    Retorna:
        list[dict]: datasets [{rows, layout}] para el ExcelReportBuilder.
    """
    work_centers = WorkCenter.objects.filter(is_removed=False)
    if isinstance(filters["work_center"], int):
        work_centers = work_centers.filter(id=filters["work_center"])

    title_date = (
        f"AL {filters['start_date'].strftime('%d/%m/%Y')}"
        if filters["start_date"] == filters["end_date"]
        else (
            f"DESDE {filters['start_date'].strftime('%d/%m/%Y')} "
            f"HASTA {filters['end_date'].strftime('%d/%m/%Y')}"
        )
    )

    datasets = []
    for work_center in work_centers.order_by("name"):
        checkings = (
            DiningChecking.objects
            .select_related(
                "employer", "conf_dining_room",
                "employer__department", "person", "person__department",
            )
            .filter(
                created__date__range=[filters["start_date"], filters["end_date"]],
                conf_dining_room__isnull=False,
                conf_dining_room__is_removed=False,
            )
            .filter(
                Q(employer__department__work_center=work_center)
                | Q(person__department__work_center=work_center)
            )
            .annotate(
                row_number=Window(
                    RowNumber(),
                    order_by=["employer__last_name", "employer__name", "-created"]
                )
            )
            .order_by("row_number", "conf_dining_room__check_name")
        )

        rows = [
            {
                "row_number": data.row_number,
                "cedula": data.employer_object.cedula,
                "fullname": data.employer_object.get_fullname(),
                "department": (
                    data.employer_object.department.name
                    if data.employer_object.department is not None else ""
                ),
                "check_turn": data.conf_dining_room.check_name,
                "check_at": data.created.strftime("%d/%m/%Y %I:%M %p"),
                "work_center": work_center.name,
            }
            for data in checkings
        ]

        totals = []
        totals_by_benefit = (
            ConfDiningRoom.objects
            .filter(
                checkings__created__date__range=[
                    filters["start_date"], filters["end_date"]
                ],
                checkings__is_removed=False,
                is_removed=False,
            )
            .annotate(total_by_benefit=Count("checkings__id"))
            .filter(total_by_benefit__gt=0)
            .order_by("check_name")
        )
        for benefit in totals_by_benefit:
            totals.append({
                "label": benefit.check_name,
                "total": benefit.total_by_benefit,
            })

        datasets.append({
            "rows": rows,
            "layout": {
                # Pestaña de la hoja con la empresa; el header mantiene el
                # texto exacto del reporte original INPROMARCA
                "sheet_title": work_center.name,
                "header_text": f"PERSONAL ASISTENTE {title_date} INPROMARCA",
                "header_rows": 1,
                "start": "A3",
                "columns": ["Trabajador", "", "", "", "", "", ""],
                "row_fields": [
                    "row_number", "cedula", "fullname", "", "department",
                    "check_turn", "check_at",
                ],
                "data_center_columns": 2,
                "merge_header_row": True,
                "row_merge": [2, 3],
                "column_widths": {
                    "A": 10, "C": 40, "E": 20, "F": 10, "G": 20,
                },
                "totals": totals,
                "totals_title": "Beneficio",
                "totals_label_offset": 2,
                "totals_value_label": "Total/Día",
                "totals_value_span": 2,
                "totals_skip": 4,
                "totals_bold": False,
            },
        })

    if not datasets:
        datasets.append({"rows": [], "layout": {
            "sheet_title": "PERSONAL ASISTENTE (sin datos en el rango)",
            "header_text": (
                f"PERSONAL ASISTENTE {title_date} INPROMARCA "
                "(sin datos en el rango)"
            ),
            "header_rows": 1,
            "start": "A3",
            "columns": ["Trabajador", "", "", "", "", "", ""],
            "row_fields": ["", "", "", "", "", "", ""],
            "data_center_columns": 2,
            "merge_header_row": True,
            "row_merge": [2, 3],
            "column_widths": {"A": 10, "C": 40, "E": 20, "F": 10, "G": 20},
            "totals": [],
            "totals_title": "Beneficio",
            "totals_label_offset": 2,
            "totals_value_label": "Total/Día",
            "totals_value_span": 2,
            "totals_skip": 4,
            "totals_bold": False,
        }})

    return datasets


def totalization_services_dataset(filters):
    """
    Arma el dataset del reporte "por totalización": secciones por
    procedencia (GhostEmployee) con su beneficio y total **por procedencia**
    (cada carga está asociada a una procedencia vía GhostServiceLoad.
    procedencia); las cargas sin procedencia (históricas/null) se agrupan en
    la sección "Sin procedencia registrada". Al final del archivo, el
    reporte salta 2 líneas e indica el total por tipo de servicio de forma
    general sobre los datos incluidos.

    Parámetros:
        filters (dict): filtros de parse_report_filters (incluye
            procedencia: id o 'all').

    Retorna:
        list[dict]: dataset único [{rows, layout}] para el ExcelReportBuilder.
    """
    loads = (
        GhostServiceLoad.objects
        .actives()
        .filter(
            date_day__range=[filters["start_date"], filters["end_date"]],
        )
        .exclude(service_type=None)
    )

    if isinstance(filters["procedencia"], int):
        loads = loads.filter(procedencia_id=filters["procedencia"])

    # Totales por procedencia y tipo de servicio (las erratas suman)
    grouped = list(
        loads.values("procedencia__name", "service_type__check_name")
        .annotate(total=Sum("quantity"))
        .order_by("procedencia__name", "service_type__check_name")
    )

    def procedencia_label(name):
        return name if name else "Sin procedencia registrada"

    total_by_service_general: Dict[str, float] = {}
    rows = []
    for item in grouped:
        procedencia_name = procedencia_label(item["procedencia__name"])
        service_name = item["service_type__check_name"]
        total = item["total"] or 0
        rows.append({
            "procedencia": procedencia_name,
            "servicio": service_name,
            "total": total,
        })
        total_by_service_general[service_name] = (
            total_by_service_general.get(service_name, 0) + total
        )

    # Si el filtro fue 'all' y no existen procedencias con cargas en el
    # rango, el dataset queda vacío (hoja con solo el header y totales nulos)
    if not rows:
        rows = [{
            "procedencia": "Sin cargas en el rango seleccionado",
            "servicio": "",
            "total": "",
        }]

    range_label = (
        filters["start_date"].strftime("%d/%m/%Y")
        if filters["start_date"] == filters["end_date"]
        else (
            f"DEL {filters['start_date'].strftime('%d/%m/%Y')} AL "
            f"{filters['end_date'].strftime('%d/%m/%Y')}"
        )
    )

    layout = {
        "sheet_title": f"TOTALIZACIÓN DE SERVICIO ENTREGADO {range_label}",
        "header_text": (
            f"REPORTE ENTREGA DE BENEFICIO ALIMENTARIO AL PERSONAL DESDE "
            f"{filters['start_date'].strftime('%d/%m/%Y')} "
            f"HASTA {filters['end_date'].strftime('%d/%m/%Y')}"
        ),
        "logo_path": str(finders.find("images/branding/logo_inpromaro_lit.png")),
        "start": "B7",
        "columns": ["", "Beneficio", "Total"],
        "row_fields": ["procedencia", "servicio", "total"],
        "section_field": "procedencia",
        "merge_key": "procedencia",
        "merge_columns": 1,
        "totals": [
            {"label": name, "total": total}
            for name, total in sorted(total_by_service_general.items())
        ],
        "totals_title": "Total por tipo de servicio",
    }
    return [{"rows": rows, "layout": layout}]


def check_dining_employer(request, card_id, *args, **kwargs):
    emp = Employee.objects.select_related("position", "department").filter(cedula=card_id).first()

    check = None
    if emp is None:
        emp = Person.objects.select_related("position", "department").filter(consecutive_code=card_id).first()
        print("Segundo intento ...")
        if emp is None:
            return JsonResponse({
                "error": True,
                "can_check": False,
                "checked": False,
                "employer": None,
                "error_message": "Cédula no encontrada o no registrada"
            })

    try:
        check = DiningChecking.objects.make_check_if_can(emp)
    except EmployerHasBeenCheckedException:
        return JsonResponse({
            "error": True,
            "can_check": True,
            "checked": False,
            "employer": None,
            "error_message": "El trabajador ya ha recibido el beneficio"
        })

    except EmployerNotPresentException:
        return JsonResponse({
            "error": True,
            "can_check": True,
            "checked": False,
            "employer": None,
            "error_message": "El trabajador no se encuentra asistente o ya ha marcado su salida"
        })

    if check is None:
        return JsonResponse({
            "error": True,
            "can_check": True,
            "checked": False,
            "employer": None,
            "error_message": "No se ha encontrado configuración de beneficio para este horario"
        })

    return JsonResponse({
        "error": False,
        "can_check": True,
        "checked": True,
        "employer": {
            "name": emp.name,
            "lastname": emp.last_name,
            "position": emp.position.position if emp.position is not None else '',
            "department": emp.department.name if emp.department is not None else '',
            "id": emp.id,
            "avatar": emp.picture.url if emp is not None and not isinstance(emp, Person) and emp.picture.name else '',
            "is_birthday": emp.is_birthday,
            "check_turn": check.conf_dining_room.check_name,
            "check_at": check.created.strftime("%I:%M %p")
        }
    })
