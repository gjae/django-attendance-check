import logging
from .models import ReportLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Obtiene la IP del cliente desde el request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_report(request, report_name: str, report_format: str, parameters: dict = None):
    """
    Registra la generación de un reporte en el log de auditoría.
    
    Args:
        request: HttpRequest de Django
        report_name: Nombre descriptivo del reporte
        report_format: "pdf" o "xlsx"
        parameters: Diccionario con los parámetros/filtros usados
    """
    try:
        format_value = ReportLog.FORMATS.pdf if report_format == "pdf" else ReportLog.FORMATS.xlsx

        ReportLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            report_name=report_name,
            report_format=format_value,
            parameters=parameters or {},
            ip_address=get_client_ip(request),
        )
        print(f"[AUDIT] Reporte registrado: {report_name} ({report_format})")
    except Exception as e:
        logger.error(f"[AUDIT ERROR] No se pudo registrar el reporte '{report_name}': {e}")
        print(f"[AUDIT ERROR] No se pudo registrar el reporte '{report_name}': {e}")

