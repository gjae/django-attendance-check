import calendar
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic.base import ContextMixin
from django.http.response import HttpResponse
from django_weasyprint import WeasyTemplateResponseMixin
from django.views.generic import TemplateView, DetailView, View
from openpyxl import Workbook
from openpyxl.worksheet.dimensions import ColumnDimension, DimensionHolder
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment, Font


from src.employees.models import Employee
from src.reports.models import TimeReport
from src.settings.models import Department
from src.clocking.models import DailyChecks, DailyCalendarObservation


class ReportLetterheadException(Exception):
    pass


class ReportBrandingLogoException(Exception):
    pass

class BaseReportMixin(ContextMixin):
    """
    Clase mixin base para la generación de reportes
    debe especificarse una propiedad letterhead_lines que será el
    encargado mostrar el membrete
    """

    def get_letterhead_lines(self):
        if not hasattr(self, "letterhead_lines"):
            raise ReportLetterheadException("letterhead_lines doesn't define")
        
        if not isinstance(self.letterhead_lines, list) and not isinstance(self.letterhead_lines, tuple):
            raise ReportLetterheadException("letterhead_lines maybe iterable object")
        

        return self.letterhead_lines
    
    def get_branding_logo(self):
        if not hasattr(self, "branding_logo") or self.branding_logo == "":
            raise ReportBrandingLogoException("branding_logo must be defined")
        
        return self.branding_logo
    
    def get_report_type(self):
        return self.report_type


    def get_context_data(self):
        context = {
            "letterheads": self.get_letterhead_lines(),
            "branding": self.get_branding_logo(),
            "report_type": self.get_report_type()
        }

        return context

class ReportByWorkerPdfView(BaseReportMixin, WeasyTemplateResponseMixin, TemplateView):
    template_name = "reports/by_worker.pdf.html"
    pdf_attachment = False
    report_type = "trabajador"
    branding_logo = "/app/src/static/images/branding/logo_inpromaro_lit.png"
    pdf_stylesheets = [
        '/app/src/static/css/bootstrap.min.css',
    ]
    letterhead_lines = (
        "INPROMAR C.A",
        "Reporte de asistencia por trabajador",
    )


    def get_pdf_filename(self):
        now = timezone.now()
        return (
            "trabajador-{at}.pdf".format(at=now.strftime("%d-%m-%Y"), )
        )
    

    def get_letterhead_lines(self):
        now = timezone.now()
        letterhead = super().get_letterhead_lines()
        
        return letterhead + (
            "<strrong>Fecha de generación {date}</strong>".format(date=now.strftime("%d/%m/%Y %I:%M %p")),
        )
    
    def get_context_data(self):
        context = super().get_context_data()
        data, total_hours = DailyChecks.objects.report_by_employee(
            int(self.request.POST.get("employer")), 
            self.request.POST.get("start_at"), 
            self.request.POST.get("end_at")
        )

        context["data"] = data
        context["total_hours"] = total_hours
        context["employer"] = Employee.objects.select_related().get(id=int(self.request.POST.get("employer")))
        context["range_start"] = datetime.strptime(self.request.POST.get("start_at"), "%Y-%m-%d")
        context["range_end"] = datetime.strptime(self.request.POST.get("end_at"), "%Y-%m-%d")
        context["observations"] = DailyCalendarObservation.objects.select_related("employer", "calendar_day").filter(
            employer_id=int(self.request.POST.get("employer")),
            calendar_day__date_day__range=[ 
                self.request.POST.get("start_at"), 
                self.request.POST.get("end_at")
            ]
        )

        return context
    
    def post(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())


class ReportByWorkerView(LoginRequiredMixin, TemplateView):
    template_name = "reports/by_worker.html"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["employers"] = Employee.objects.only_actives().order_by("last_name", "name")
        return context


class ReportByDepartmentPdfView(BaseReportMixin, WeasyTemplateResponseMixin, TemplateView):
    template_name = "reports/by_department.pdf.html"
    pdf_attachment = False
    report_type = "trabajador"
    branding_logo = "/app/src/static/images/branding/logo_inpromaro_lit.png"
    pdf_stylesheets = [
        '/app/src/static/css/bootstrap.min.css',
    ]
    letterhead_lines = (
        "INPROMAR C.A",
        "Reporte de asistencia por departamento",
    )


    def get_pdf_filename(self):
        now = timezone.now()
        return (
            "departamento-{at}.pdf".format(at=now.strftime("%d-%m-%Y"), )
        )
    

    def get_letterhead_lines(self):
        now = timezone.now()
        letterhead = super().get_letterhead_lines()
        
        return letterhead + (
            "<strrong>Fecha de generación {date}</strong>".format(date=now.strftime("%d/%m/%Y %I:%M %p")),
        )
    
    def get_context_data(self):
        context = super().get_context_data()
        data, total_hours = DailyChecks.objects.report_by_employee(None, self.request.POST.get("start_at"), self.request.POST.get("end_at"), department=int(self.request.POST.get("department")))

        context["data"] = data
        context["total_hours"] = total_hours
        context["department"] = Department.objects.select_related().get(id=int(self.request.POST.get("department")))
        context["range_start"] = datetime.strptime(self.request.POST.get("start_at"), "%Y-%m-%d")
        context["range_end"] = datetime.strptime(self.request.POST.get("end_at"), "%Y-%m-%d")
        context["observations"] = DailyCalendarObservation.objects.select_related("employer", "calendar_day").filter(
            employer__department_id=int(self.request.POST.get("department")),
            calendar_day__date_day__range=[ 
                self.request.POST.get("start_at"), 
                self.request.POST.get("end_at")
            ]
        )
        return context
    
    def post(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())


class ReportByDepartmentView(LoginRequiredMixin, TemplateView):
    template_name = "reports/by_department.html"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["departments"] = Department.objects.all().order_by("name")
        return context


class ReportExcelMixin(LoginRequiredMixin, View):

    def get_footer(self, total_hours):
        num_fields = len(self.get_headers())
        fields = ["Horas trabajadas"]

        for i in range(num_fields - 2):
            fields.append(" ")

        fields.append(total_hours)

        return fields

    def before(self, ws):
        pass

    def post_processing(self, data, sheet, wb):
        pass

    def post(self, request, *args, **kwargs):
        workbook = Workbook()
        headers = self.get_headers()
        ws = workbook.active
        self.before(ws)
        ws.title = self.get_sheet_title()

        ws.append(headers)
        data, total_hours = self.get_report_content() 

        for record in data:
            ws.append(self.process_row(record))

        ws.append(self.get_footer(total_hours))

        self.post_processing(data, ws, workbook)


        dim_holder = DimensionHolder(worksheet=ws)

        for col in range(ws.min_column, ws.max_column + 1):
            dim_holder[get_column_letter(col)] = ColumnDimension(ws, min=col, max=col, width=20)
        
        ws.column_dimensions = dim_holder
        file_name = self.get_file_name()
        response = HttpResponse(content_type="application/ms-excel")
        content = "attachment; filename = {0}".format(file_name)
        response["Content-Disposition"] = content
        workbook.save(response)
        return response
    

class ReportBrandMixin:

    def get_headlines(self, department, model_id):
        return ""
    
    def before(self, ws):
        now = timezone.now()
        ws.merge_cells("A1:A6")
        img = Image("/app/src/static/images/branding/logo_inpromaro_lit.png")
        ws.add_image(img, "A1")
        ws.merge_cells("B1:G6")
        department = None
        if "department" in self.request.POST:
            department = Department.objects.get(id=self.request.POST.get("department"))

        else:
            department = Employee.objects.select_related("department").get(id=int(self.request.POST.get("employer"))).department
        
        ws["B1"].alignment = Alignment(horizontal="center", vertical="center")
        ws["B1"].font = Font(bold=True, size=13, name="Arial")

        ws["B1"].value = self.get_headlines(department, int(self.request.POST.get("department", self.request.POST.get("employer"))))
        for i in range(6):
            ws.append([" ", " ", " ", " ", " ", " ", " "])


class ReportWorkerExcel(ReportBrandMixin, ReportExcelMixin):
    def get_headlines(self, department, model_id):
        now = timezone.now()
        
        employer = Employee.objects.get(id=model_id)
        start_at = datetime.strptime(self.request.POST.get("start_at"), "%Y-%m-%d")
        end_at = datetime.strptime(self.request.POST.get("end_at"), "%Y-%m-%d")
        return (
            " Reporte por departamento \n"
            f"Departamento: {department.name} \n"
            f"Trabajador: {employer.name} {employer.last_name} - {employer.cedula} \n"
            f"Desde {start_at.strftime('%d/%m/%Y')} hasta {end_at.strftime('%d/%m/%Y')} \n"
            "Fecha de generación: {0} \n ".format(now.strftime("%d/%m/%Y"))
        )
    
    def get_headers(self):
        return [
            "Fecha", 
            "Hora de entrada",
            "Hora de salida",
            "Total de horas"
        ]
    
    def process_row(self, record):
        return [
            record["created"].strftime("%d/%m/%Y"),
            record["start_at"],
            record["end_at"],
            record["abs_total_hours"]
        ]

    def get_sheet_title(self):
        return "Reporte por trabajador"

    def get_file_name(self):
        return "{at}_reporte_por_trabajador.xlsx".format(
            at=calendar.timegm(timezone.now().timetuple())
        )

    def get_report_content(self):
        return DailyChecks.objects.report_by_employee( int(self.request.POST.get("employer")), self.request.POST.get("start_at"), self.request.POST.get("end_at"))
    
    def post_processing(self, data, sheet, wb):
        observations = DailyCalendarObservation.objects.select_related("employer", "calendar_day").filter(
            employer_id=int(self.request.POST.get("employer")),
            calendar_day__date_day__range=[ 
                self.request.POST.get("start_at"), 
                self.request.POST.get("end_at")
            ]
        )
        
        observation_sheet = wb.create_sheet("Observaciones")
        observation_sheet.append([
            "Nombre y apellido",
            "Cédula",
            "Fecha",
            "Descripción",
        ])
        for observation in observations:
            observation_sheet.append([
                observation.employer.get_fullname(),
                observation.employer.cedula,
                observation.calendar_day.date_day.strftime("%d/%m/%Y"),
                observation.description
            ])

        dim_holder = DimensionHolder(worksheet=observation_sheet)
        for col in range(observation_sheet.min_column, observation_sheet.max_column + 1):
            dim_holder[get_column_letter(col)] = ColumnDimension(observation_sheet, min=col, max=col, width=20)
        
    
class ReportDepartmentExcel(ReportBrandMixin, ReportExcelMixin):

    def get_headlines(self, department, model_id):
        now = timezone.now()
        start_at = datetime.strptime(self.request.POST.get("start_at"), "%Y-%m-%d")
        end_at = datetime.strptime(self.request.POST.get("end_at"), "%Y-%m-%d")
        return (
            " Reporte por departamento \n"
            f"Departamento: {department.name} \n"
            f"Desde {start_at.strftime('%d/%m/%Y')} hasta {end_at.strftime('%d/%m/%Y')} \n"
            "Fecha de generación: {0} \n ".format(now.strftime("%d/%m/%Y"))
        )
    
    def get_headers(self):
        return [
            "Cédula", 
            "Nombre",
            "Apellido",
            "Cargo",
            "Total de horas"
        ]
    
    def process_row(self, record):
        return [
            record["employer"].cedula,
            record["employer"].name,
            record["employer"].last_name,
            record["employer"].position.position,
            record["abs_total_hours"]
        ]

    def get_sheet_title(self):
        return "Reporte por departamento"

    def get_file_name(self):
        return "{at}_reporte_por_departamento.xlsx".format(
            at=calendar.timegm(timezone.now().timetuple())
        )
    
    def get_report_content(self):
        return DailyChecks.objects.report_by_employee(
            None, 
            self.request.POST.get("start_at"), 
            self.request.POST.get("end_at"), 
            department=int(self.request.POST.get("department"))
        )
    
    
    def post_processing(self, data, sheet, wb):
        observations = DailyCalendarObservation.objects.select_related("employer", "calendar_day").filter(
            employer__department_id=int(self.request.POST.get("department")),
            calendar_day__date_day__range=[ 
                self.request.POST.get("start_at"), 
                self.request.POST.get("end_at")
            ]
        )
        
        observation_sheet = wb.create_sheet("Observaciones")
        observation_sheet.append([
            "Nombre y apellido",
            "Cédula",
            "Fecha",
            "Descripción",
        ])
        for observation in observations:
            observation_sheet.append([
                observation.employer.get_fullname(),
                observation.employer.cedula,
                observation.calendar_day.date_day.strftime("%d/%m/%Y"),
                observation.description
            ])

        dim_holder = DimensionHolder(worksheet=observation_sheet)
        for col in range(observation_sheet.min_column, observation_sheet.max_column + 1):
            dim_holder[get_column_letter(col)] = ColumnDimension(observation_sheet, min=col, max=col, width=20)
        
    