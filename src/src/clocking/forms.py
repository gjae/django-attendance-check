import logging
from django import forms
from django.core.exceptions import ObjectDoesNotExist

from src.employees.models import Employee
from src.clocking.models import DailyChecks
from src.settings.models import WorkCenter, ClientConfig
from .exceptions import EmployeeDoenstBelongsToThisWorkCenterException

class ClientMarkCheckForm(forms.Form):
    entrypoint = forms.ModelChoiceField(queryset=ClientConfig.objects.select_related("work_center").filter(work_center__isnull=False))
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
            employee = Employee.objects.select_related("department", "department__work_center").get(cedula=self.cleaned_data["cedula"])
            current_work_center = self.cleaned_data.get("entrypoint").work_center
            if employee.department.work_center != current_work_center and not self.cleaned_data.get("entrypoint").allow_clocking_from_another_workcenter:
                raise EmployeeDoenstBelongsToThisWorkCenterException("El trabajador no pertenece a este centro")
        except ObjectDoesNotExist as e:
            log.exception(e)
            return None
        
        return DailyChecks.objects.checking_user(employee, entrypoint=self.cleaned_data.get("entrypoint", None))