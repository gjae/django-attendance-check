from django.urls import path, include

from src.reports import views

urlpatterns = [
    path("worker/", views.ReportByWorkerView.as_view(), name="reports.by.worker"),
    path("worker/pdf/", views.ReportByWorkerPdfView.as_view(), name="reports.by.worker.pdf"),
    path("department/", views.ReportByDepartmentView.as_view(), name="reports.by.department"),
    path("department/pdf/", views.ReportByDepartmentPdfView.as_view(), name="reports.by.department.pdf"),
    path("worker/excel/", views.ReportWorkerExcel.as_view(), name="reports.by.worker.excel"),
    path("department/excel/", views.ReportDepartmentExcel.as_view(), name="reports.by.department.excel"),
]
