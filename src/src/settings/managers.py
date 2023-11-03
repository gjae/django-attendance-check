from django.db import models



class ClientConfigManager(models.Manager):
    
    def get_enabled_clients(self):
        """
        Recupera los puntos de entradas activos
        """
        from src.settings.models import ClientConfig

        return self.filter(status=ClientConfig.STATUS.enabled)
    


    def is_enabled(self, ip: str) -> bool:
        """
        Verifica si un punto de entrada, dada una IP
        esta activo
        """

        enableds = self.get_enabled_clients().values_list("client_ip", flat=True)

        return ip in list(enableds)
    


class DepartmentManager(models.Manager):
    pass