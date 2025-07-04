from django.urls import path

from src.peladoydescabezado import views

urlpatterns = [
    path("progress/", views.save_progress, name="update_progress"),
    path("<int:cedula>/fetchUser/", views.fetch_user , name="fetch_employer"),
    path("save/", views.load_weight, name="save_weight"),
    path("reports/", views.create_report, name="reports_generator"),
    path("todayReport", views.weight_save_current_report, name="weight_current_report"),
    path("todayReport/pdf/", views.generate_pdf, name="weight_current_pdf"),
]