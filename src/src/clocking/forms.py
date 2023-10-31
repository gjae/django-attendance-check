import logging
from django import forms
from django.core.exceptions import ObjectDoesNotExist

from src.employees.models import Employee
from src.clocking.models import DailyChecks

class ClientMarkCheckForm(forms.Form):
    cedula = forms.IntegerField(
        label="Cédula escaneada del QR",
        error_messages={
            "required": "No se ha escaneado correctamente el QR"
        }
    )


    def clean_cedula(self):
        cedula = self.cleaned_data["cedula"]
        if not Employee.objects.allow_checking(cedula):
            raise forms.ValidationError(
                "La cédula que intenta escanear no se encuentra registrada o está desactivada"
            )
        
        return cedula
    

    def save(self):
        log = logging.getLogger(__name__)
        employee = None
        
        try:
            employee = Employee.objects.get(cedula=self.cleaned_data["cedula"])
        except ObjectDoesNotExist as e:
            log.exception(e)
            return None
        
        return DailyChecks.objects.checking_user(employee)