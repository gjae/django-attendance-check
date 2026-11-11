from django.shortcuts import render
from datetime import datetime, time
import time
import unicodedata
from typing import Dict, Optional
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.staticfiles import finders
from django.forms.models import model_to_dict
from django.views.generic import TemplateView
from django.http.response import HttpResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Window, Q, Count
from django.db.models.functions import RowNumber

from src.dining_room.models import DiningChecking, ConfDiningRoom
from src.dining_room.models import GhostEmployee, GhostServiceLoad
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


REPORT_VIEW_PERMISSIONS = (
    # Permisos de vista válidos para generar reportes de gestión de
    # comedor: el permiso propio del proxy "Gestión" (donde vive el
    # modal de descarga) o el permiso clásico de configuración de
    # turnos de comedor. Basta con TENER UNO de los dos.
    "dining_room.view_diningroomproxymodel",
    "dining_room.view_conf_diningroom",
)


def may_generate_dining_reports(user):
    """Indica si el usuario puede generar reportes de gestión de comedor.

    El requisito es tener CUALQUIERA de los permisos de vista definidos
    en REPORT_VIEW_PERMISSIONS (vista del proxy Gestión o vista de la
    configuración de turnos de comedor); NO exige tener todos.

    Parámetros:
        user (User): usuario autenticado de la petición.

    Retorna:
        bool: True si el usuario cuenta con al menos uno de los permisos
        de vista listados en REPORT_VIEW_PERMISSIONS.
    """
    return any(
        user.has_perm(perm)
        for perm in REPORT_VIEW_PERMISSIONS
    )


@login_required
def report_dining_today_excel(request, *args, **kwargs):
    """
    Handler del builder de reportes de comedor (dining_room.reportering).

    Genera el reporte según los parámetros de la descarga hecha desde el
    modal de gestión de comedor (DiningRoomProxyModel):

    - report_type: 'empresa' (default, "Por empresa") o 'totalizacion'
      (visible como "Reporte general").
    - print_date: fecha única (compatibilidad con el enlace anterior).
    - start_date / end_date: rango de fechas (end_date inclusive).
    - work_center: id de empresa o 'all' (solo reporte por empresa).
    - procedencia: id de GhostEmployee o 'all' (solo reporte general;
      filtra las secciones por procedencia en el archivo).

    Requiere sesión activa y AL MENOS UN permiso de vista del módulo
    (ver REPORT_VIEW_PERMISSIONS: vista del proxy Gestión o vista de
    configuración de turnos de comedor).
    Los servicios entregados a procedencias (GhostServiceLoad, cargas
    originales y erratas, estas últimas suman) se reportan únicamente en
    el reporte general (totalización), sin afectar los cálculos de
    asistencia del personal fijo.

    Parámetros:
        request (HttpRequest): petición con los filtros de reporte.

    Retorna:
        HttpResponse: archivo Excel (o tabla HTML en salida display)
        auditado con log_report.
    """
    if not may_generate_dining_reports(request.user):
        raise PermissionDenied(
            "No tiene permisos para generar reportes de gestión de comedor."
        )

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
            "Reporte general de servicios de comedor"
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
    La totalización de cada hoja es POR empresa y discrimina por tipo de
    beneficio: chequeos de comedor de esa empresa + servicios cargados a
    procedencias relacionadas a ella (GhostEmployee.work_center, erratas
    incluidas). Los registros de modelos fantasma nunca generan filas de
    chequeo (solo totalización) y las procedencias sin empresa solo
    aparecen en el reporte general. Los datos de totalización NO se
    mezclan con el reporte general (eso vive exclusivamente ahí).

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

        # Totalización de ESTA empresa (discriminada por tipo de beneficio):
        # servicios entregados por chequeo de comedor + servicios cargados a
        # procedencias relacionadas a la empresa (GhostEmployee.work_center,
        # cargas originales y erratas, estas últimas suman). Las
        # procedencias sin empresa no se atribuyen a ninguna hoja: solo
        # aparecen en el reporte general (totalización); registros fantasma
        # no generan filas de chequeo, solo totales.
        #
        # El conteo por chequeo se arma DESDE DiningChecking agrupado por
        # beneficio (join único por lado employer/person, NOTA: los FK
        # employer y person son single-valued y no multiplican filas);
        # contar via ConfDiningRoom.checkings duplicaba el valor porque cada
        # llamada a filter() sobre la relación multi-valor checkings__ crea
        # un JOIN independiente y el mismo chequeo entraba 2 veces.
        totals_map: Dict[str, float] = {}

        checks_by_benefit = (
            DiningChecking.objects
            .filter(
                created__date__range=[
                    filters["start_date"], filters["end_date"]
                ],
                is_removed=False,
                conf_dining_room__isnull=False,
                conf_dining_room__is_removed=False,
            )
            .filter(
                Q(employer__department__work_center=work_center)
                | Q(person__department__work_center=work_center)
            )
            .values("conf_dining_room__check_name")
            .annotate(total=Count("id"))
        )
        for check in checks_by_benefit:
            benefit_name = check["conf_dining_room__check_name"]
            totals_map[benefit_name] = (
                totals_map.get(benefit_name, 0) + (check["total"] or 0)
            )

        ghost_by_benefit = (
            GhostServiceLoad.objects
            .actives()
            .filter(
                date_day__range=[filters["start_date"], filters["end_date"]],
            )
            .exclude(service_type=None)
            .filter(procedencia__work_center=work_center)
            .values("service_type__check_name")
            .annotate(total=Sum("quantity"))
        )
        for ghost in ghost_by_benefit:
            benefit_name = ghost["service_type__check_name"]
            totals_map[benefit_name] = (
                totals_map.get(benefit_name, 0) + (ghost["total"] or 0)
            )

        totals = [
            {"label": benefit_name, "total": benefit_total}
            for benefit_name, benefit_total in sorted(totals_map.items())
            if benefit_total > 0
        ]

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


# Empresa que SIEMPRE va de primera en el bloque de empresas del reporte
# general (comparación exacta del nombre normalizado; no afecta nombres
# que solo CONTIENEN esta cadena, ej: "Transporte INPROMAR")
EMPRESA_SIEMPRE_PRIMERA = "INPROMAR"


def normalizar_nombre(texto):
    """Normaliza un nombre para comparar empresa vs procedencia.

    Quita acentos/diacríticos, pasa a mayúsculas y colapsa espacios,
    de modo que "FABRICA DE HIELO EL CARMEN" y "Fábrica de Hielo el
    Carmen" coincidan (mismas palabras escritas distinto).

    Parámetros:
        texto (str): nombre a normalizar (None se trata como "").

    Retorna:
        str: nombre normalizado para comparación.
    """
    sin_acentos = unicodedata.normalize(
        "NFKD", str(texto or "")
    ).encode("ascii", "ignore").decode("ascii")
    return " ".join(sin_acentos.upper().split())


def totalization_services_dataset(filters):
    """Arma el dataset del reporte "general" (internamente totalización) en
    UN SOLO bloque (sin título de bloque; el encabezado de la hoja ya
    indica "REPORTE GENERAL DE SERVICIO ENTREGADO..."), con las secciones
    identificadas por su nombre y en este orden:

    1. Secciones por EMPRESA: entregas por CHEQUEO ORDINARIO (asistencia)
       atribuidas a la empresa del chequeado, en formato empresa -
       beneficio - total, + las cargas de las procedencias HOMÓNIMAS (si
       una o más procedencias llevan el mismo nombre normalizado que la
       empresa se fusionan en UNA sola sección; el resto de las
       procedencias conserva su sección propia). TODAS las empresas
       (WorkCenter no eliminadas) aparecen, también en 0 si no registran
       entregas; un chequeo sin empresa en AMBOS lados cae en el bucket
       defensivo "Sin empresa" (no ocurre con usuarios asociados por
       trabajador->departamento).
    2. Secciones por PROCEDENCIA: alimentadas ÚNICAMENTE por sus cargas
       (GhostServiceLoad; erratas suman) — NUNCA se mezclan con las
       entregas por chequeo. TODAS las procedencias no fusionadas con su
       empresa homónima aparecen, con o sin cargas en el rango (0 por
       defecto en cada beneficio del universo); las cargas sin
       procedencia (históricas) forman la sección "Sin procedencia
       registrada".

    Al final, UNA sola totalización general por tipo de servicio: TODAS
    las cargas del rango (ligadas o no a una empresa) + TODAS las
    entregas reales del rango, calculada independiente del detalle para
    que nunca haya doble conteo ni mezcla de sumas; siempre visible, con
    0 en los beneficios sin movimiento del rango (universo de beneficios
    = cargas ∪ reales ∪ catálogo activo). Las filas de beneficios, en
    TODAS las secciones y en la totalización, se ordenan por HORARIO DE
    ENTREGA (start_time del turno de comedor, del más temprano al más
    tardío); los sin horario conocido van al final, alfabéticos entre
    ellos.

    Parámetros:
        filters (dict): filtros de parse_report_filters (incluye
            procedencia: id o 'all').

    Retorna:
        list[dict]: dataset único [{rows, layout}] para el
        ExcelReportBuilder.
    """
    specific_id = (
        filters["procedencia"]
        if isinstance(filters["procedencia"], int)
        else None
    )

    def suma_en(mapa, clave, nombre, valor):
        """Acumula valor de un beneficio en el par clave/respuesta dado.

        Parámetros:
            mapa (dict): registro clave → {beneficio: total}.
            clave: clave de mapa a actualizar (creada si falta).
            nombre (str): tipo de beneficio.
            valor (float): cantidad a sumar (None cuenta como 0).

        Retorna:
            None.
        """
        mapa.setdefault(clave, {})
        mapa[clave][nombre] = mapa[clave].get(nombre, 0) + (valor or 0)

    # Cargas del rango (las erratas SUMAN porque errata ya es una carga
    # nueva y solo se operan las quantities)
    all_loads = (
        GhostServiceLoad.objects
        .actives()
        .filter(
            date_day__range=[filters["start_date"], filters["end_date"]],
        )
        .exclude(service_type=None)
    )
    detail_loads = (
        all_loads.filter(procedencia_id=specific_id) if specific_id else all_loads
    )

    # Cargas por procedencia y beneficio (con filtro, solo para el detalle)
    cargas_por_procedencia: Dict[Optional[int], Dict[str, int]] = {}
    service_schedule: Dict[str, Optional[time]] = {}

    def registrar_beneficio(nombre, horario):
        """Registra un beneficio en el universo con su horario de entrega.

        Guarda el horario MÁS TEMPRANO visto para el mismo nombre (un
        beneficio no debería repetir horario; si ocurriera manda el más
        temprano). Los horarios alimentan el orden por horario de entrega
        de las filas del reporte.

        Parámetros:
            nombre (str): nombre del beneficio (check_name); None ignora.
            horario (time | None): start_time del turno de comedor (None
                = sin horario conocido; ordena al final).

        Retorna:
            None.
        """
        if nombre is None:
            return
        previo = service_schedule.get(nombre)
        if previo is None or (
            horario is not None and horario < previo
        ):
            service_schedule[nombre] = horario

    for item in (
        detail_loads.values("procedencia_id", "service_type__check_name")
        .annotate(total=Sum("quantity"))
    ):
        suma_en(
            cargas_por_procedencia,
            item["procedencia_id"],
            item["service_type__check_name"],
            item["total"],
        )
    # Horario de entrega de los beneficios cargados (query aparte, sin
    # agregación: sumar el horario al values del agrupado dividiría los
    # totales del mismo beneficio con horarios distintos)
    for nombre, horario in all_loads.values_list(
        "service_type__check_name", "service_type__start_time"
    ):
        registrar_beneficio(nombre, horario)

    # Entregas reales por chequeo ordinario (asistencia) del rango
    filtered_checks = DiningChecking.objects.filter(
        created__date__range=[filters["start_date"], filters["end_date"]],
        is_removed=False,
        conf_dining_room__isnull=False,
        conf_dining_room__is_removed=False,
    )
    # Entregas reales atribuidas en PYTHON a la empresa del chequeado (NO
    # por rutas SQL separadas: un chequeo de carnet tiene employer NULL y
    # con isnull=True del path employer caería como "sin empresa" aunque
    # su person esté asociado a una empresa por trabajador->departamento,
    # además de poder contar doble entre rutas). Preferencia: employer
    # (personal fijo) y si no resuelve, person (Department.work_center);
    # mismo criterio que employer_object del modelo / reporte por empresa.
    checks_flat = filtered_checks.values(
        "conf_dining_room__check_name",
        "conf_dining_room__start_time",
        "employer__department__work_center__id",
        "person__department__work_center__id",
    )
    real_por_empresa: Dict[int, Dict[str, int]] = {}
    real_sin_empresa: Dict[str, int] = {}
    for item in checks_flat:
        nombre = item["conf_dining_room__check_name"]
        registrar_beneficio(nombre, item["conf_dining_room__start_time"])
        employer_id = item["employer__department__work_center__id"]
        wc_id = (
            employer_id
            if employer_id is not None
            else item["person__department__work_center__id"]
        )
        if wc_id is None:
            # Chequeo sin empresa en AMBOS lados (no debería ocurrir con
            # usuarios asociados por trabajador->departamento; bucket
            # defensivo "Sin empresa")
            real_sin_empresa[nombre] = (
                real_sin_empresa.get(nombre, 0) + 1
            )
            continue
        real_por_empresa.setdefault(wc_id, {})
        real_por_empresa[wc_id][nombre] = (
            real_por_empresa[wc_id].get(nombre, 0) + 1
        )

    # Universo de beneficios: consolidado en los bucles anteriores + el
    # catálogo de beneficios activos y no eliminados, para que el rango
    # SIEMPRE liste todas las procedencias/empresas con sus filas de
    # beneficios (en 0 los que no registran movimiento en el rango)
    for nombre, horario in ConfDiningRoom.objects.filter(
        is_removed=False,
        is_active__isnull=True,
    ).values_list("check_name", "start_time"):
        registrar_beneficio(nombre, horario)

    # Orden de beneficios: por HORARIO DE ENTREGA (start_time del turno de
    # comedor, del más temprano al más tardío); los sin horario conocido
    # van al final, alfabéticos entre ellos
    orden_beneficios = sorted(
        service_schedule,
        key=lambda nombre: (service_schedule[nombre] or time.max, nombre),
    )

    # Total por tipo de servicio: TODAS las cargas del rango (ligadas o no
    # a una empresa, erratas incluidas) + TODAS las entregas reales del
    # rango; calculado independiente del detalle para que nunca haya doble
    # conteo (ej: procedencias distintas ligadas a la misma empresa). Con
    # filtro de procedencia específica no se reduce
    total_by_service_general: Dict[str, float] = {}
    for item in (
        all_loads.values("service_type__check_name")
        .annotate(total=Sum("quantity"))
    ):
        nombre = item["service_type__check_name"]
        total_by_service_general[nombre] = (
            total_by_service_general.get(nombre, 0) + (item["total"] or 0)
        )
    for por_beneficio in real_por_empresa.values():
        for nombre, cantidad in por_beneficio.items():
            total_by_service_general[nombre] = (
                total_by_service_general.get(nombre, 0) + cantidad
            )
    for nombre, cantidad in real_sin_empresa.items():
        total_by_service_general[nombre] = (
            total_by_service_general.get(nombre, 0) + cantidad
        )

    # Todas las procedencias no eliminadas; con filtro específico el
    # detalle se limita a esa sección
    all_ghosts = list(
        GhostEmployee.objects.filter(is_removed=False).order_by("name", "id")
    )
    ordered_ghosts = [
        ghost for ghost in all_ghosts
        if specific_id is None or ghost.id == specific_id
    ]

    rows = []

    def seccion(label, por_beneficio):
        """Agrega al bloque las filas de una sección.

        Cada sección cubre el universo completo de beneficios, con 0 en
        los que no registran movimiento en el rango.

        Parámetros:
            label (str): nombre de la empresa o procedencia (columna
                fusionada verticalmente).
            por_beneficio (dict): beneficio → total de la sección.

        Retorna:
            None.
        """
        for nombre in orden_beneficios:
            rows.append({
                "procedencia": label,
                "servicio": nombre,
                "total": por_beneficio.get(nombre, 0),
            })

    # Fusión por nombre: si una o más procedencias del detalle llevan el
    # MISMO nombre normalizado que una empresa, se muestra UNA sola
    # sección con las cargas de esas procedencias + los chequeos
    # ordinarios de la empresa (evita duplicar visualmente el nombre, ej:
    # "FABRICA DE HIELO EL CARMEN" empresa y "FÁBRICA DE HIELO EL
    # CARMEN" procedencia). Las demás procedencias conservan su sección
    # propia (cada una la suya aunque varias apunten a la misma empresa)
    procedencias_por_nombre: Dict[str, list] = {}
    for ghost in ordered_ghosts:
        procedencias_por_nombre.setdefault(
            normalizar_nombre(ghost.name), []
        ).append(ghost)
    ghosts_fusionados = set()

    # Primeras secciones: EMPRESAS, alimentadas por las entregas por
    # chequeo ordinario + las cargas de sus procedencias homónimas (las
    # cargas de procedencias NO homónimas NO se mezclan aquí). La empresa
    # fija (EMPRESA_SIEMPRE_PRIMERA) va PRIMERA en todo momento; el resto:
    # centro actual (is_current_center) primero, luego alfabético
    work_centers = list(WorkCenter.objects.filter(is_removed=False))
    work_centers.sort(
        key=lambda wc: (
            normalizar_nombre(wc.name)
            != normalizar_nombre(EMPRESA_SIEMPRE_PRIMERA),
            not wc.is_current_center,
            wc.name,
            wc.id,
        )
    )
    for work_center in work_centers:
        por_beneficio = dict(real_por_empresa.get(work_center.id) or {})
        homonimas = procedencias_por_nombre.get(
            normalizar_nombre(work_center.name), []
        )
        for ghost in homonimas:
            ghosts_fusionados.add(ghost.id)
            for nombre, cantidad in (
                cargas_por_procedencia.get(ghost.id) or {}
            ).items():
                por_beneficio[nombre] = (
                    por_beneficio.get(nombre, 0) + cantidad
                )
        seccion(work_center.name, por_beneficio)

    # Chequeos sin empresa en AMBOS lados al final del grupo de empresas
    if real_sin_empresa:
        seccion("Sin empresa", real_sin_empresa)

    # Si no existen empresas registradas (ni chequeos sin empresa),
    # placeholder para que el bloque no quede vacío tras su encabezado
    if not rows:
        rows.append({
            "procedencia": "Sin empresas registradas",
            "servicio": "",
            "total": "",
        })

    # Luego: PROCEDENCIAS, alimentadas SOLO por sus cargas (las entregas
    # por chequeo ordinario NO se mezclan aquí); las fusionadas con su
    # empresa homónima ya se muestran dentro de la sección de esa empresa
    for ghost in ordered_ghosts:
        if ghost.id in ghosts_fusionados:
            continue
        seccion(ghost.name, cargas_por_procedencia.get(ghost.id) or {})

    # Cargas sin procedencia (históricas) al final del grupo de procedencias
    cargas_sin_procedencia = cargas_por_procedencia.get(None)
    if cargas_sin_procedencia:
        seccion("Sin procedencia registrada", cargas_sin_procedencia)

    # Si no existen procedencias registradas (ni cargas sin procedencia),
    # placeholder al final para que el grupo de procedencias no quede vacío
    if not ordered_ghosts and not cargas_sin_procedencia:
        rows.append({
            "procedencia": "Sin procedencias registradas",
            "servicio": "",
            "total": "",
        })

    range_label = (
        filters["start_date"].strftime("%d/%m/%Y")
        if filters["start_date"] == filters["end_date"]
        else (
            f"DEL {filters['start_date'].strftime('%d/%m/%Y')} AL "
            f"{filters['end_date'].strftime('%d/%m/%Y')}"
        )
    )

    layout = {
        "sheet_title": f"REPORTE GENERAL DE SERVICIO ENTREGADO {range_label}",
        "header_text": (
            # Salto de línea forzado tras "AL PERSONAL": el título baja a
            # una 2da línea con el rango de fechas (el header del general
            # usa wrap_text=True, así que Excel respeta el salto)
            "REPORTE ENTREGA DE BENEFICIO ALIMENTARIO AL PERSONAL\n"
            f"DESDE {filters['start_date'].strftime('%d/%m/%Y')} "
            f"HASTA {filters['end_date'].strftime('%d/%m/%Y')}"
        ),
        # Ancho del título multi-línea: 4 columnas (B..E), UN rango
        # combinado por parte (B1:E1 y B2:E2) en vez del bloque único
        # que cubría todo el ancho calculado por longitud del texto
        "header_span": 4,
        "logo_path": str(
            finders.find("images/branding/logo_reportes_excel.JPG")
        ),
        # Logo de alta resolución (1080x964): reescalado proporcional a
        # ~166px de alto para un header compacto (misma proporción, sin
        # distorsión); las celdas ancla se adaptan al tamaño final
        "logo_height_px": 166,
        "start": "B7",
        "columns": ["", "Beneficio", "Total"],
        "row_fields": ["procedencia", "servicio", "total"],
        "section_field": "procedencia",
        "merge_key": "procedencia",
        "merge_columns": 1,
        # Única totalización general por beneficio, SIEMPRE visible, con 0
        # en los beneficios sin movimiento del rango; label alineada bajo
        # "Beneficio" y valor bajo "Total" (offset 1 desde la col inicial)
        "totals": [
            {"label": nombre, "total": total_by_service_general.get(nombre, 0)}
            for nombre in orden_beneficios
        ],
        "totals_label_offset": 1,
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
