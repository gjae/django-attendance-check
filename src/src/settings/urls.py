from django.urls import path

from src.settings import views

urlpatterns = [
    path("", views.hello_world, name="client.index")
]
