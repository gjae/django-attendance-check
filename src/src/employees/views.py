from django.shortcuts import render
from django.views.generic import DetailView
from django.conf import settings
from django_weasyprint import WeasyTemplateResponseMixin
from src.peladoydescabezado.models import Person

# Create your views here.

from src.employees.models import Employee

class MyDetailView(DetailView):
    # vanilla Django DetailView
    template_name = 'carnets/carnet_print.html'
    model = Employee

    def get_model(self):
        if self.request.GET.get("src") != "pelado":
            return Employee
        
        return Person

class PrintCartnetView(WeasyTemplateResponseMixin, MyDetailView):
    pdf_attachment = False

    def get_pdf_filename(self):
        employer = self.get_context_data().get("current_carnet_data")
        return f"{employer.name}_{employer.last_name}_{employer.cedula}.pdf"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_carnet_data"] = None
        
        print("Generando carnet para ", self.request.GET)
        if self.request.GET.get("src") != "pelado":
            context["current_carnet_data"] = Employee.objects.filter(id=self.kwargs.get("pk")).first()
        else:
            context["current_carnet_data"] = Person.objects.filter(id=self.kwargs.get("pk")).first()

        return context
    


class PrintCartnetFromPeladoView(PrintCartnetView):
    model = Person
    extra_context = {"force_default_carnet": True}