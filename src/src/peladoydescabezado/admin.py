from django.utils.html import mark_safe
from django.contrib import admin
import logging
from django.contrib import messages
from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils import timezone

from .models import Person, Table

# Register your models here.


@admin.action(description="Desactivar mesas")
def disable_tables(modeladmin, request, queryset):
    queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        "Las mesas seleccionadas fueron desactivadas correctamente",
        messages.SUCCESS
    )


@admin.action(description="Activar mesas")
def enable_tables(modeladmin, request, queryset):
    queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        "Las mesas seleccionadas fueron activadas correctamente",
        messages.SUCCESS
    )


@admin.action(description="Archivar mesas")
def archive_tables(modeladmin, request, queryset):
    queryset.update(archived_at=timezone.now())
    modeladmin.message_user(
        request,
        "Las mesas seleccionadas fueron archivadas correctamente",
        messages.SUCCESS
    )


@admin.register(Person)
class PeopleModelAdmin(ModelAdmin):
    list_display = [
       "personal_photo", "identity", "names", "lastnames", "created", "phone"
    ]

    fieldsets = (
        ("Datos Personales", {
            "fields": (
                ("names", "lastnames", "identity"),
            ),
        }),
        ("Identificación", {
            "fields": (
                ("identity_pic", "personal_pic"),
            ),
        }),
        ("Datos Laborales", {
            "fields": (
                ("department", "position", ), "daily_basket", 
            )
        })
    )

    def personal_photo(self, obj):
        if obj.personal_pic is None:
            return ""
        try:
            return mark_safe(
                f"<div>"
                f'<img src="{obj.personal_pic.url}" alt="{obj.names}_picture" class="w-10 h-10 rounded-full" loading="lazy" decoding="async">'
                f"</div>"
            )
        except Exception as e:
            return mark_safe(
                f"<div>"
                f'<img src="/static/images/branding/logo_inpromaro_lit.png" alt="default" class="w-10 h-10 rounded-full" loading="lazy" decoding="async">'
                f"</div>"
            )
        
    personal_photo.short_description = "Foto"
    

@admin.register(Table)
class TableModelAdmin(ModelAdmin):
    list_display = [
       "id", "created", "description", "max_workers", "category", "is_active"
    ]

    list_filter = ["is_active", "category"]
    list_per_page = 18
    actions = [disable_tables, enable_tables, archive_tables]

    fieldsets = (
        (None, {
            "fields": (
                "is_active", 
            )
        }),
        
        (None, {
            "fields": (
                "description",
                "category",
                "max_workers",
            ),
        }),
    )
    

    def get_queryset(self, request):
        return super().get_queryset(request).filter(archived_at__isnull=True)

    def has_delete_permission(self, request, obj = None):
        return False