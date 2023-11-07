from django.urls import path

from . import views

urlpatterns = [
    path("<int:pk>/", views.PrintCartnetView.as_view(), name="carnets.print"),
]
