from django.http import HttpResponse
from src.settings.models import ClientConfig

class ClientMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        """
        Verificar si la ruta incluye la porción "admin", en caso de ser
        así se retorna la respuesta por defecto, en caso de que no lo tenga 
        es porque la petición llega desde un cliente 

        en ese caso se debe consutar la lista de IP de clientes para verificar si 
        continua con la petición o se retorna un error
        """

        if "admin" in request.get_full_path() or "error" in request.get_full_path():
            return self.get_response(request)
        
        if ClientConfig.objects.is_enabled(request.META.get("REMOTE_ADDR", "0.0.0.0")):
            return self.get_response(request)
        

        msg = "Este cliente no se encuentra activo"
        return HttpResponse(msg, status=404)