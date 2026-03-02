from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ReportLog


@admin.register(ReportLog)
class ReportLogAdmin(ModelAdmin):
    list_display = [
        "created",
        "user",
        "report_name",
        "report_format",
        "ip_address",
    ]

    list_filter = [
        "report_format",
        "user",
    ]

    search_fields = [
        "report_name",
        "user__username",
        "user__first_name",
        "user__last_name",
    ]

    readonly_fields = [
        "created",
        "user",
        "report_name",
        "report_format",
        "parameters",
        "ip_address",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
