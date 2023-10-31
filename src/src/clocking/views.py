from django.views.generic import FormView

from src.clocking.forms import ClientMarkCheckForm
from src.clocking.mixins import JSONResponseMixin
from src.clocking.models import DailyChecks

class ClientMarkCheckFormView(JSONResponseMixin, FormView):
    form_class = ClientMarkCheckForm

    def form_invalid(self, form):
        errors = {f: e.get_json_data() for f, e in form.errors.items()}

        return self.render_to_json_response({
            "error": True,
            "message": errors,
            "checking_type": None
        })

    def form_valid(self, form):
        cheecking = form.save()
            
        return self.render_to_json_response({
            "error": False,
            "message": "Chequeo realizado correctamente",
            "checking_type": "ENTRADA" if cheecking.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada else "SALIDA",
            "user_data": {
                "name": cheecking.employee.get_fullname(),
                "position": cheecking.employee.position.position,
                "department": "SISTEMAS",
                "photo": cheecking.employee.picture.url
            }
        })
