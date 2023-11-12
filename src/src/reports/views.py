from datetime import datetime
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic.base import ContextMixin
from django_weasyprint import WeasyTemplateResponseMixin
from django.views.generic import TemplateView, DetailView


from src.employees.models import Employee
from src.reports.models import TimeReport
from src.settings.models import Department

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
            "<strrong>Fecha de generación {date}</strong>".format(date=now.strftime("%d/%m/%Y %I:%m %p")),
        )
    
    def get_context_data(self):
        context = super().get_context_data()
        data = (
            TimeReport
            .objects
            .filter(employer_id=int(self.request.POST.get("employer")))
            .filter(
                created__range=[
                    self.request.POST.get("start_at"), 
                    self.request.POST.get("end_at")
                ]
            )
            .select_related(
                "employer"
            )
        )

        total_hours = 0
        for d in data:
            total_hours += d.abs_total_hours

        context["data"] = data
        context["total_hours"] = total_hours
        context["employer"] = Employee.objects.select_related().get(id=int(self.request.POST.get("employer")))
        context["range_start"] = datetime.strptime(self.request.POST.get("start_at"), "%Y-%m-%d")
        context["range_end"] = datetime.strptime(self.request.POST.get("end_at"), "%Y-%m-%d")
        return context
    
    def post(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())


class ReportByWorkerView(LoginRequiredMixin, TemplateView):
    template_name = "reports/by_worker.html"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["employers"] = Employee.objects.only_actives()
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
            "<strrong>Fecha de generación {date}</strong>".format(date=now.strftime("%d/%m/%Y %I:%m %p")),
        )
    
    def get_context_data(self):
        context = super().get_context_data()
        data = (
            TimeReport
            .objects
            .filter(employer__department_id=int(self.request.POST.get("department")))
            .filter(
                created__range=[
                    self.request.POST.get("start_at"), 
                    self.request.POST.get("end_at")
                ]
            )
            .select_related(
                "employer"
            )
        )

        total_hours = 0
        for d in data:
            total_hours += d.abs_total_hours

        context["data"] = data
        context["total_hours"] = total_hours
        context["department"] = Department.objects.select_related().get(id=int(self.request.POST.get("department")))
        context["range_start"] = datetime.strptime(self.request.POST.get("start_at"), "%Y-%m-%d")
        context["range_end"] = datetime.strptime(self.request.POST.get("end_at"), "%Y-%m-%d")
        return context
    
    def post(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())


class ReportByDepartmentView(LoginRequiredMixin, TemplateView):
    template_name = "reports/by_department.html"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["departments"] = Department.objects.all()
        return context
