import logging
from django.views.generic import FormView

from src.clocking.forms import ClientMarkCheckForm
from src.clocking.mixins import JSONResponseMixin
from src.clocking.models import DailyChecks

from src.clocking.exceptions import CheckingTooRecentException, CheckingOutputTooRecentException

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
        

        return self.render_to_json_response({
            "error": False,
            "message": "Chequeo realizado correctamente",
            "checking_type": "ENTRADA" if cheecking.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada else "SALIDA",
            "error_type": None,
            "user_data": {
                "name": cheecking.employee.get_fullname(),
                "position": cheecking.employee.position.position,
                "department": "SISTEMAS",
                "photo": cheecking.employee.picture.url if cheecking.employee.picture is not None and cheecking.employee.picture.name else None
            }
        })
