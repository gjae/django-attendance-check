import logging
from django.http import HttpResponse
from django.utils import translation
from django.conf import settings
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
        log = logging.getLogger(__name__)

        log.info(f"Ip request: {request.META.get('REMOTE_ADDR', '0.0.0.0')} / {request.META.get('HTTP_X_REAL_IP', '0.0.0.0')}")
        request.current_entrypoint = None
        if "admin" in request.get_full_path() or "error" in request.get_full_path() or "media" in request.get_full_path() or "employers" in request.get_full_path():
            print("MEDIA AQUI")
            return self.get_response(request)
        
        if "images" in request.get_full_path():
            return self.get_response(request)
        
        if "reports" in request.get_full_path():
            return self.get_response(request)
        
        if "media" in request.get_full_path():
            return self.get_response(request)

        if "peladoydescabezado" in request.get_full_path():
            return self.get_response(request)

        
        enabled, point =  ClientConfig.objects.is_enabled(request.META.get("HTTP_X_REAL_IP", "0.0.0.0"))
        if enabled:
            request.current_entrypoint = point
            return self.get_response(request)
        

        msg = "Este cliente no se encuentra activo"
        return HttpResponse(msg, status=404)
    