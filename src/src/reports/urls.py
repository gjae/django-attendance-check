from django.urls import path, include

from src.reports import views

urlpatterns = [
    path("worker/", views.ReportByWorkerView.as_view(), name="reports.by.worker"),
]
