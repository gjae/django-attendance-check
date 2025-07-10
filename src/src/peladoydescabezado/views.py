import io
from datetime import datetime
from django.db import transaction
from django.db.models import Prefetch
from django.http.response import JsonResponse, HttpResponseNotAllowed, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from weasyprint import HTML, CSS

from weasyprint.text.fonts import FontConfiguration

from src.peladoydescabezado.models import Control, ControlDetail, Person, CATEGORIES, Department
from src.peladoydescabezado.forms import LoadWeightForm
from src.peladoydescabezado.utils import get_xlsx_report_template, generate_rport_xlsx_simple, attendance_by_department_xlsx, attendance_by_personal_xlsx
from src.peladoydescabezado.exceptions import WorkerIsNotPresentException
from src.clocking.models import DailyCalendarObservation

@csrf_exempt
@login_required
def save_progress(request, *args, **kwargs):

    if request.method.lower() != "post":
        return HttpResponseNotAllowed()

    turn = request.POST.get("load_turn", None)
    if turn is not None:
        turn = int(turn)
    date = request.POST.get("load_date", datetime.now().date())
    control = Control.objects.control_by_turn(request.user, load_turn=turn, load_date=(date if turn is not None else None))
    with transaction.atomic():
        if request.POST.get("action", "add") == "add":
            detail, _ = ControlDetail.objects.update_or_create(
                control=control,
                farm_id=int(request.POST.get("farm")),
                pool_id=int(request.POST.get("pool")),
                defaults={
                    "total_weight_received": float(request.POST.get("weight", 0.00))
                }
            )
            weightness = [int(i) for i in request.POST.getlist("weightness") if int(i) > 0]
            if len(weightness) > 0:
                detail.weightness.set(weightness)
            else:
                detail.weightness.clear()
        else:
            ControlDetail.objects.filter(control=control, farm_id=int(request.POST.get("farm")), pool_id=int(request.POST.get("pool"))).delete()

        return JsonResponse({
            "error": False,
            "message": "Ok"
        })
    

@csrf_exempt
@login_required
def fetch_user(request, cedula, *args, **kwargs):
    employer = Person.objects.filter(identity=cedula).first()

    if employer is None:
        return JsonResponse({"error": True, "message": "Cédula no registrada", "data": {}})
    
    return JsonResponse({
        "error": False,
        "message": "Ok",
        "data": {
            "id": employer.id,
            "name": employer.names,
            "lastname": employer.lastnames
        }
    })


@csrf_exempt
@login_required
def load_weight(request, *args, **kwargs):
    if request.method.lower() != "post":
        return HttpResponseNotAllowed()
    
    form = LoadWeightForm(request.POST)
    try:
        if form.is_valid():
            form.save()
            return JsonResponse({
                "error": False,
                "message": "Pesaje guardado correctamente"
            })
    except WorkerIsNotPresentException:
        return JsonResponse({
            "error": True,
            "message": "El trabajador no se encuentra presente o no marcó su entrada"
        })



    return JsonResponse({
        "error": True,
        "message": "Error al intentar guardar los datos del pesaje"
    })


def weight_save_current_report(request, *args, **kwargs):
    # week = int(request.GET.get("semana", "")[request.GET.get("semana", "").index("-")+2:])
    # year = int(request.GET.get("semana", "").split("-")[0])
    date_from = request.GET.get("fecha_inicio_rango", datetime.now().date())
    date_end = request.GET.get("fecha_fin_rango", datetime.now().now())
    turn = int(request.GET.get("turno", 1))
    if isinstance(date_from, str):
        date_from = datetime.strptime(date_from, "%Y-%m-%d")

    if isinstance(date_end, str):
        date_end = datetime.strptime(date_end, "%Y-%m-%d")

    template = get_xlsx_report_template(date_from=date_from, date_end=date_end, turn=turn)
    
    # Configurar la respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="relacion-diaria-{datetime.now().timestamp()}.xlsx"'
    
    # Guardar el libro en la respuesta
    template.save(response)
    return response


def generate_pdf(request, *args, **kwargs):
    # Renderizar la plantilla HTML con el contexto proporcionado
    date = request.GET.get("fecha_inicio", datetime.now().date().strftime("%Y-%m-%d"))
    data = Person.objects.get_employers_with_production(date=date, category=int(request.GET.get("category", 0)))
    basckets_list = [u.num_basckets for u in data]
    num_max_totalization_cells = max(basckets_list if len(basckets_list) > 0 else [0, ])
    totalization_cells = range(0, num_max_totalization_cells)
    context = {
        "data": data,
        "weight_total": sum([u.total for u in data if u is not None and u.total is not None]),
        "num_cells": totalization_cells,
        "avg_cell_space": 100 / num_max_totalization_cells if num_max_totalization_cells > 0 else 1,
        "date": datetime.strptime(date, "%Y-%m-%d"),
        "code": "IMP-PRO-FOR-006",
        "version": 1,
        "category": int(request.GET.get("category", 0)),
        "category_text": CATEGORIES[int(request.GET.get("category", 0))],
        "total_basckets": sum([u.num_basckets for u in data]),
        "controls": Control.objects.filter(date_upload=date).prefetch_related(
            Prefetch(
                "details",
                queryset=ControlDetail.objects.prefetch_related("weightness").select_related(
                    "farm",
                    "pool",
                ),
                to_attr="control_details"
            )
        )
    }
    html_string = render_to_string("reports/pleadoydescabezado/general.pdf.html", context)
    
    # Configuración de fuentes (opcional)
    font_config = FontConfiguration()
    
    # Crear un objeto HTML de WeasyPrint
    html = HTML(string=html_string,  base_url=request.build_absolute_uri())
    
    # Crear un buffer de bytes para el PDF
    pdf_buffer = io.BytesIO()
    
    # Escribir el PDF en el buffer
    html.write_pdf(
        target=pdf_buffer,
        font_config=font_config,
        stylesheets=None,  # Puedes añadir hojas de estilo CSS adicionales aquí
        presentational_hints=True
    )
    
    # Crear la respuesta HTTP
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=CONTROL_ENTREGA_VALOR_AGREGADO_{datetime.now().timestamp()}.pdf'
    response['X-Frame-Options'] = 'ALLOW-FROM *'
    response['Content-Type'] = 'application/pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    
    return response

def _simple_excel(request):
    date = request.GET.get("fecha_inicio", datetime.now().date().strftime("%Y-%m-%d"))
    data = Person.objects.get_employers_with_production(date=date, category=int(request.GET.get("category", 0)))
    basckets_list = [u.num_basckets for u in data]
    num_max_totalization_cells = max(basckets_list if len(basckets_list) > 0 else [0, ])
    totalization_cells = range(0, num_max_totalization_cells)
    context = {
        "data": data,
        "weight_total": sum([u.total for u in data if u is not None and u.total is not None]),
        "num_cells": totalization_cells,
        "avg_cell_space": 100 / num_max_totalization_cells if num_max_totalization_cells > 0 else 1,
        "date": datetime.strptime(date, "%Y-%m-%d"),
        "code": "IMP-PRO-FOR-006",
        "version": 1,
        "num_max_totalization_cells": num_max_totalization_cells,
        "category": int(request.GET.get("category", 0)),
        "category_text": CATEGORIES[int(request.GET.get("category", 0))],
        "total_basckets": sum([u.num_basckets for u in data]),
        "controls": Control.objects.filter(created__date=date).prefetch_related(
            Prefetch(
                "details",
                queryset=ControlDetail.objects.prefetch_related("weightness").select_related(
                    "farm",
                    "pool",
                ),
                to_attr="control_details"
            )
        )
    }

    book = generate_rport_xlsx_simple(context)
    # Configurar la respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="valor-agregado-{datetime.now().timestamp()}.xlsx"'
    
    # Guardar el libro en la respuesta
    book.save(response)
    return response




def generate_assistence_pdf(request, *args, **kwargs):
    # Renderizar la plantilla HTML con el contexto proporcionado
    date = request.GET.get("fecha_inicio_rango", datetime.now().date().strftime("%Y-%m-%d"))
    until_date = request.GET.get("fecha_fin_rango",datetime.now().date().strftime("%Y-%m-%d") )
    department = None
    if request.GET.get("department", None) is not None and request.GET.get("department") != "":
        department = Department.objects.filter(id=int(request.GET.get("department", 1))).first()
    else:
        department = Department.objects.first()

    data, total_hours, total_days_by_user  = Person.objects.report_by_department(
        from_date=date, until_date=until_date, department=department.id)
    
    context = {
        "data": data,
        "department": department,
        "range_start": datetime.strptime(date, "%Y-%m-%d"),
        "range_end": datetime.strptime(until_date, "%Y-%m-%d"),
        "branding": "file:///app/src/static/images/branding/logo_inpromaro_lit.png",
        "total_hours": total_hours,
        "total_days_by_user": total_days_by_user,
        "show_metadata": False,
        "observations": DailyCalendarObservation.objects.select_related("employer", "calendar_day", "person").filter(
            person__department_id=int(request.GET.get("department")),
            calendar_day__date_day__range=[ 
                request.GET.get("fecha_inicio_rango"), 
                request.GET.get("fecha_fin_rango")
            ]
        ),
        "letterheads": (
            "INPROMAR C.A",
            "Reporte de asistencia por trabajador",
        ) + (
            "<strrong>Fecha de generación {date}</strong>".format(date=datetime.now().strftime("%d/%m/%Y %I:%M %p")),
            "Departamento: {}".format(department.name),
            "Desde <strong>{}</strong> hasta <strong>{}</strong>".format(
                datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y"),
                datetime.strptime(until_date, "%Y-%m-%d").strftime("%d/%m/%Y"),
            )
        )
    }
    html_string = render_to_string("reports/by_department.pdf.html", context)
    
    # Configuración de fuentes (opcional)
    font_config = FontConfiguration()
    
    # Crear un objeto HTML de WeasyPrint
    html = HTML(string=html_string,  base_url=request.build_absolute_uri() )
    
    # Crear un buffer de bytes para el PDF
    pdf_buffer = io.BytesIO()
    
    # Escribir el PDF en el buffer
    html.write_pdf(
        target=pdf_buffer,
        font_config=font_config,
        presentational_hints=True,
        stylesheets=[
            # Puedes incluir archivos CSS externos o CSS interno
            '/app/src/static/css/bootstrap.min.css',
        ]

    )
    
    # Crear la respuesta HTTP
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=CONTROL_ENTREGA_VALOR_AGREGADO_{datetime.now().timestamp()}.pdf'
    response['X-Frame-Options'] = 'ALLOW-FROM *'
    response['Content-Type'] = 'application/pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    
    return response

def generate_assistence_xlsx(request, *args, **kwargs):
    date = request.GET.get("fecha_inicio_rango", datetime.now().date().strftime("%Y-%m-%d"))
    until_date = request.GET.get("fecha_fin_rango",datetime.now().date().strftime("%Y-%m-%d") )
    department = None
    if request.GET.get("department", None) is not None and request.GET.get("department") != "":
        department = Department.objects.filter(id=int(request.GET.get("department", 1))).first()
    else:
        department = Department.objects.first()

    data, total_hours, total_days_by_user  = Person.objects.report_by_department(
        from_date=date, until_date=until_date, department=department.id)
    
    context = {
        "data": data,
        "department": department,
        "range_start": datetime.strptime(date, "%Y-%m-%d"),
        "range_end": datetime.strptime(until_date, "%Y-%m-%d"),
        "branding": "file:///app/src/static/images/branding/logo_inpromaro_lit.png",
        "total_hours": total_hours,
        "total_days_by_user": total_days_by_user,
        "show_metadata": False,
        "observations": DailyCalendarObservation.objects.select_related("employer", "calendar_day", "person").filter(
            person__department_id=int(request.GET.get("department")),
            calendar_day__date_day__range=[ 
                request.GET.get("fecha_inicio_rango"), 
                request.GET.get("fecha_fin_rango")
            ]
        ),

    }
    book = attendance_by_department_xlsx(context)
    # Configurar la respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="asistencia-por-departamento-{datetime.now().timestamp()}.xlsx"'
    
    # Guardar el libro en la respuesta
    book.save(response)
    return response




def generate_personal_pdf(request, *args, **kwargs):
    # Renderizar la plantilla HTML con el contexto proporcionado
    date = request.GET.get("fecha_inicio_rango", datetime.now().date().strftime("%Y-%m-%d"))
    until_date = request.GET.get("fecha_fin_rango",datetime.now().date().strftime("%Y-%m-%d") )
    department = None
    if request.GET.get("department", None) is not None and request.GET.get("department") != "":
        department = Department.objects.filter(id=int(request.GET.get("department", 1))).first()
    else:
        department = Department.objects.first()

    person = Person.objects.get(id=int(request.GET.get("person_id")))
    data, total_hours, total_days_by_user  = Person.objects.report_by_employee(
        int(request.GET.get("person_id")), 
        request.GET.get("fecha_inicio_rango"), 
        request.GET.get("fecha_fin_rango"),
        is_employer_model=False
    )
    
    context = {
        "data": data,
        "department": department,
        "range_start": datetime.strptime(date, "%Y-%m-%d"),
        "range_end": datetime.strptime(until_date, "%Y-%m-%d"),
        "branding": "file:///app/src/static/images/branding/logo_inpromaro_lit.png",
        "total_hours": total_hours,
        "total_days_by_user": total_days_by_user,
        "show_metadata": False,
        "observations": DailyCalendarObservation.objects.select_related("employer", "calendar_day", "person").filter(
            person_id=int(request.GET.get("person_id")),
            calendar_day__date_day__range=[ 
                request.GET.get("fecha_inicio_rango"), 
                request.GET.get("fecha_fin_rango")
            ]
        ),
        "letterheads": (
            "INPROMAR C.A",
            "Reporte de asistencia por trabajador",
        ) + (
            "<strrong>Fecha de generación {date}</strong>".format(date=datetime.now().strftime("%d/%m/%Y %I:%M %p")),
            "Reporte del trabajador: {}".format(person.get_fullname()),
            "Desde <strong>{}</strong> hasta <strong>{}</strong>".format(
                datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y"),
                datetime.strptime(until_date, "%Y-%m-%d").strftime("%d/%m/%Y"),
            )
        )
    }
    html_string = render_to_string("reports/by_worker.pdf.html", context)
    
    # Configuración de fuentes (opcional)
    font_config = FontConfiguration()
    
    # Crear un objeto HTML de WeasyPrint
    html = HTML(string=html_string,  base_url=request.build_absolute_uri() )
    
    # Crear un buffer de bytes para el PDF
    pdf_buffer = io.BytesIO()
    
    # Escribir el PDF en el buffer
    html.write_pdf(
        target=pdf_buffer,
        font_config=font_config,
        presentational_hints=True,
        stylesheets=[
            # Puedes incluir archivos CSS externos o CSS interno
            '/app/src/static/css/bootstrap.min.css',
        ]

    )
    
    # Crear la respuesta HTTP
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=CONTROL_ENTREGA_VALOR_AGREGADO_{datetime.now().timestamp()}.pdf'
    response['X-Frame-Options'] = 'ALLOW-FROM *'
    response['Content-Type'] = 'application/pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    
    return response


def generate_personal_xlsx(request, *args, **kwargs):
    date = request.GET.get("fecha_inicio_rango", datetime.now().date().strftime("%Y-%m-%d"))
    until_date = request.GET.get("fecha_fin_rango",datetime.now().date().strftime("%Y-%m-%d") )
    department = None


    person = Person.objects.select_related('department').get(id=int(request.GET.get("person_id")))
    data, total_hours, total_days_by_user  = Person.objects.report_by_employee(
        int(request.GET.get("person_id")), 
        request.GET.get("fecha_inicio_rango"), 
        request.GET.get("fecha_fin_rango"),
        is_employer_model=False
    )
    
    context = {
        "data": data,
        "department": person.department,
        "range_start": datetime.strptime(date, "%Y-%m-%d"),
        "range_end": datetime.strptime(until_date, "%Y-%m-%d"),
        "branding": "file:///app/src/static/images/branding/logo_inpromaro_lit.png",
        "total_hours": total_hours,
        "total_days_by_user": total_days_by_user,
        "show_metadata": False,
        "person": person,
        "observations": DailyCalendarObservation.objects.select_related("employer", "calendar_day", "person").filter(
            person_id=int(request.GET.get("person_id")),
            calendar_day__date_day__range=[ 
                request.GET.get("fecha_inicio_rango"), 
                request.GET.get("fecha_fin_rango")
            ]
        ),

    }
    book = attendance_by_personal_xlsx(context)
    # Configurar la respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="asistencia-por-persona-{datetime.now().timestamp()}.xlsx"'
    
    # Guardar el libro en la respuesta
    book.save(response)
    return response

@login_required
def create_report(request, *args, **kwargs):
    report_type = request.GET.get("tipo_reporte")
    response = None
    if report_type == "simple":
        if request.GET.get("report_type", "pdf") == "pdf":
            return generate_pdf(request)
        elif request.GET.get("report_type", "pdf") == "xlsx":
            return _simple_excel(request)


    elif report_type == "rango":
        response = weight_save_current_report(request)

    elif report_type == "assistence":
        if request.GET.get("report_type", "pdf") == "pdf":
            response = generate_assistence_pdf(request)
        elif request.GET.get("report_type", "pdf") == "xlsx":
            response = generate_assistence_xlsx(request)

    
    elif report_type == "personal":
        if request.GET.get("report_type", "pdf") == "pdf":
            response = generate_personal_pdf(request)
        elif request.GET.get("report_type", "pdf") == "xlsx":
            response = generate_personal_xlsx(request)

    return response