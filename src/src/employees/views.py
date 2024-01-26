from django.shortcuts import render
from django.views.generic import DetailView
from django.conf import settings
from django_weasyprint import WeasyTemplateResponseMixin

# Create your views here.

from src.employees.models import Employee

class MyDetailView(DetailView):
    # vanilla Django DetailView
    template_name = 'carnets/carnet_print.html'
    model = Employee


class PrintCartnetView(WeasyTemplateResponseMixin, MyDetailView):
    pdf_filename = 'carnet.pdf'
    pdf_attachment = False


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_carnet_data"] = Employee.objects.filter(id=self.kwargs.get("pk")).first()
        return context
    