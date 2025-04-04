from django.db import models



class ClientConfigManager(models.Manager):
    
    def get_enabled_clients(self, ip):
        """
        Recupera los puntos de entradas activos
        """
        from src.settings.models import ClientConfig

        return self.filter(client_ip=ip).filter(status=ClientConfig.STATUS.enabled)
    


    def is_enabled(self, ip: str) -> bool:
        """
        Verifica si un punto de entrada, dada una IP
        esta activo
        """

        points = self.get_enabled_clients(ip).filter(work_center__is_current_center=True).values("client_ip", "pk").first()

        return points is not None , points
    


class DepartmentManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related("work_center")