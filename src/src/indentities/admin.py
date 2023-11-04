from django.contrib import admin
from django.http.request import HttpRequest
from unfold.admin import ModelAdmin

# Register your models here.

from .models import Identity
from .forms import IdentificationModelForm

@admin.register(Identity)
class IdentityModelAdmin(ModelAdmin):
    form = IdentificationModelForm
    list_display = [
        "id", "belongs_to", "cedula", "created", "emited_at", "expire_at", "expirable"
    ]
    search_fields = [
        "id"
    ]

    def get_queryset(self, request: HttpRequest):
        return super().get_queryset(request).select_related("employer")


    def cedula(self, obj):
        return obj.employer.cedula
    
    def belongs_to(self, obj):
        return obj.employer.get_fullname()
    
    belongs_to.short_description = "Pertenece a"