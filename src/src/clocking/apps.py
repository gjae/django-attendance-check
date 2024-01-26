from django.apps import AppConfig


class ClockingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.clocking"
    verbose_name = "Calendario del sistema"
    def ready(self):
        try:
            import src.clocking.signals  # noqa: F401
        except ImportError:
            pass
