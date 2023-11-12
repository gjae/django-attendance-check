from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView


class ReportByWorkerView(TemplateView):
    template_name = "reports/by_worker.html"