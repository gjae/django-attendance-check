import logging
import time
from datetime import datetime
from django.views.generic import FormView
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt

from src.clocking.forms import ClientMarkCheckForm
from src.clocking.mixins import JSONResponseMixin
from src.clocking.models import DailyChecks
from src.settings.models import ClientConfig

from src.clocking.exceptions import CheckingTooRecentException, CheckingOutputTooRecentException, EmployeeDoenstBelongsToThisWorkCenterException

class ClientMarkCheckFormView(JSONResponseMixin, FormView):
    form_class = ClientMarkCheckForm

    def form_invalid(self, form):
        errors = {f: e.get_json_data() for f, e in form.errors.items()}

        return self.render_to_json_response({
            "error": True,
            "message": errors,
            "checking_type": None,
            "error_type": "identity"
        })

    def form_valid(self, form):
        cheecking = None
        log = logging.getLogger(__name__)

        try:
            cheecking = form.save()
        except CheckingTooRecentException as e:
            log.exception(e)
            return self.render_to_json_response({
                "error": True,
                "error_type": "timeout",
                "message": {
                    "cedula": [{"message": "Ya ha marcado su entrada correctamente. Debe esperar al menos 3 minutos para poder volver a marcar su salida"}, ]
                },
                "checking_type": None
            })
        except CheckingOutputTooRecentException as e:
            log.exception(e)
            return self.render_to_json_response({
                "error": True,
                "error_type": "timeout",
                "message": {
                    "cedula": [{"message": "Su salida ya fue marcada, debe esperar al menos 3 minutos para volver a marcar su próximo entrada"}, ]
                },
                "checking_type": None
            })
        except EmployeeDoenstBelongsToThisWorkCenterException as e:
            log.exception(e)
            return self.render_to_json_response({
                "error": True,
                "error_type": "timeout",
                "message": {
                    "cedula": [{"message": "El trabajador no pertenece a esta empresa y no se permite chequeos de asistencia para trabajadores de otras empresas"}, ]
                },
                "checking_type": None
            })

        

        return self.render_to_json_response({
            "id": cheecking.id,
            "error": False,
            "message": "Chequeo realizado correctamente",
            "checking_type": "ENTRADA" if cheecking.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada else "SALIDA",
            "error_type": None,
            "timestamp": time.mktime(cheecking.checking_time.timetuple()),
            "user_data": {
                "id": cheecking.employee.id,
                "name": cheecking.employee.get_fullname(),
                "position": cheecking.employee.position.position,
                "department": "SISTEMAS",
                "photo": cheecking.employee.picture.url if cheecking.employee.picture is not None and cheecking.employee.picture.name else None
            },
            "recheck": False
        })




def list_clocking_points(request, *args, **kwargs):
    clockings = ClientConfig.objects.select_related("work_center").filter(work_center__isnull=False)
    response = []

    for point in clockings:
        response.append({
            "id": point.pk,
            "name": point.description,
            "work_center": {
                "id": point.work_center.pk,
                "name": point.work_center.name
            }
        })


    return JsonResponse({"data": response})


@csrf_exempt
def recheck_clocking(request, *args, **kwargs):
    if request.method.lower() != "post":
        return HttpResponseNotAllowed(["post", ])
    
    response = []
    clocking_ids = {}
    users = [int(uid) for uid in request.POST.getlist("users")]
    types = [t for t in request.POST.getlist("types")]
    dt = [datetime.fromtimestamp(float(t)) for t in request.POST.getlist("times")]


    for idx, clock_id in enumerate(request.POST.getlist("ids")):
        clocking_ids[int(clock_id)] = (users[idx], types[idx], dt[idx])

    clockings = DailyChecks.objects.filter(id__in=list(clocking_ids.keys())).select_related("employee", "daily")
    for clocking in clockings:
        data = clocking_ids[clocking.id]
        d_response = {
            "clocking_id": clocking.id, 
            "timestamp": time.mktime(clocking.checking_time.timetuple()), 
            "user_id": 
            clocking.employee_id, 
            "checked": data[0] == clocking.employee_id and data[1].upper() == clocking.check_type_as_str().upper()
        }
        response.append(d_response)

    return JsonResponse({"error": False, "message": response})