from django.urls import path

from src.clocking import views

urlpatterns = [
    path("check/", views.ClientMarkCheckFormView.as_view(), name="clocking.checking"),
    path("listPoints/", views.list_clocking_points, name="clocking.list_points"),
    path("rechects/", views.recheck_clocking, name="clocking.recheck")
]
