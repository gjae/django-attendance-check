from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.employees"
    verbose_name = "Registro de trabajadores"

    def ready(self):
        try:
            import src.employees.signals  # noqa: F401
        except ImportError:
            pass

