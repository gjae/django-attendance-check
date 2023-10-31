from django.urls import path

from src.clocking import views

urlpatterns = [
    path("check/", views.ClientMarkCheckFormView.as_view(), name="clocking.checking"),
]
