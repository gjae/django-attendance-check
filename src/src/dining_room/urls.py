from django.urls import path

from . import views

urlpatterns = [
    path("<int:card_id>/check/", views.check_dining_employer, name="dining_room.check"),
    path("index/", views.index, name="dining_room.index"),
    path("todayChecks/", views.default_today_last_checks, name="dining_room.today_check"),
    path("reports/", views.report_dining_today_excel, name="dining_room.today_report_xlsx")
]
