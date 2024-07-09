from django.shortcuts import render
from datetime import datetime
import time
from django.http.response import JsonResponse
from django.forms.models import model_to_dict
from django.views.generic import TemplateView
from django.http.response import HttpResponse
from django.db.models import Window
from django.db.models.functions import RowNumber

from openpyxl import Workbook
from openpyxl.styles.borders import Border, Side
from openpyxl.styles import Alignment, Font

from src.dining_room.models import DiningChecking
from src.employees.models import Employee
from src.clocking.models import DailyChecks
from unfold.views import UnfoldModelAdminViewMixin

# Create your views here.

class ReportAdminView(UnfoldModelAdminViewMixin, TemplateView):
    title = "Gestion de reportes de comedor"  # required: custom page header title
    permissions_required = (
        "dining_room.view_dining_room",
    ) # required: tuple of permissions
    template_name = "dining_room/report_admin_template.html"


def report_dining_today_excel(request, *args, **kwargs):
    workbook = Workbook()
    ws = workbook.active
    current_date = datetime.now()
    today_data = DailyChecks.objects.select_related("employee").filter(daily__date_day=current_date.date()).annotate(
        row_number=Window(
            RowNumber(),
            order_by=["-checking_time", "employee__name", "employee__last_name"]
        )
    ).order_by("row_number")
    thin_border = Border(
        left=Side(style='thin'), 
        right=Side(style='thin'), 
        top=Side(style='thin'), 
        bottom=Side(style='thin')
    )
    aligment = Alignment(horizontal="center", vertical="center")
    font_subtitle = Font(name="Arial", size=14)
    font = Font(
        name="Calibri",
        size=11,
        bold=True
    )
    data_row_from = 4

    ws.merge_cells("B1:E1")
    ws.merge_cells("C3:D3")
    ws["B1"].value = f"PERSONAL ASISTENTE AL {current_date.strftime('%d/%m/%Y')} INPROMARCA"
    ws["C3"].value = "Trabajador"
    ws["C3"].border = thin_border
    ws["B3"].border = thin_border
    ws["D3"].border = thin_border
    ws["E3"].border = thin_border

    ws["B1"].font = font
    ws["C3"].alignment = aligment
    ws["B1"].alignment= aligment
    ws["C3"].font= font_subtitle

    for data in today_data:
        ws[f"B{data_row_from}"].value = data.row_number
        ws[f"C{data_row_from}"].value = data.employee.get_fullname()
        ws[f"E{data_row_from}"].value = data.get_checking_type_display()

        ws[f"B{data_row_from}"].border = thin_border
        ws[f"C{data_row_from}"].border = thin_border
        ws[f"D{data_row_from}"].border = thin_border
        ws[f"E{data_row_from}"].border = thin_border

        ws[f"B{data_row_from}"].alignment = aligment
        ws[f"E{data_row_from}"].alignment = aligment
        data_row_from = data_row_from + 1

    ws.column_dimensions["C"].width = 30
    response = HttpResponse(content_type="application/ms-excel")
    content = "attachment; filename =Comedor_{0}.xlsx".format(
        int(time.mktime(current_date.timetuple()))
    )
    response["Content-Disposition"] = content
    workbook.save(response)
    return response

def index(request, *args, **kwargs):
    today_checks = DiningChecking.objects.today_checks()

    return render(
        request, 
        "dining_room/index.html", 
        {"today_checks": today_checks}
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


def check_dining_employer(request, card_id, *args, **kwargs):
    emp = Employee.objects.select_related("position", "department").filter(cedula=card_id).first()
    if emp is None:
        return JsonResponse({
            "error": True, 
            "can_check": False, 
            "checked": False,
            "employer": None
        })
    
    check = DiningChecking.objects.make_check_if_can(emp)

    if check is None:
        return JsonResponse({
            "error": True, 
            "can_check": True, 
            "checked": False,
            "employer": None
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
            "avatar": emp.picture.url if emp is not None and emp.picture.name else '',
            "is_birthday": emp.is_birthday,
            "check_turn": check.conf_dining_room.check_name,
            "check_at": check.created.strftime("%I:%M %p")
        }
    })