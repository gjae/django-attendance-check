import logging
from django import forms
from django.core.exceptions import ObjectDoesNotExist

from src.employees.models import Employee
from src.clocking.models import DailyChecks, DailyCalendarObservation, DailyChecksProxyModelAdmin
from src.settings.models import WorkCenter, ClientConfig
from src.peladoydescabezado.models import Person
from .exceptions import EmployeeDoenstBelongsToThisWorkCenterException, EmployeeDesactivedException

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
        if Employee.objects.allow_checking(cedula):
            return cedula
        
        elif Person.objects.allow_checking(cedula):
            return cedula
        
        raise forms.ValidationError(
            "La cédula que intenta escanear no se encuentra registrada o está desactivada"
        )
        
    def _get_employee_obj(self, cedula):
        try:
            employee = Employee.objects.select_related("department", "department__work_center").get(cedula=cedula)
            return employee
        except ObjectDoesNotExist as e:
            return Person.objects.select_related("department", "department__work_center").get(identity=cedula)

    def save(self):
        log = logging.getLogger(__name__)
        employee = None
        
        try:
            employee = self._get_employee_obj(self.cleaned_data.get("cedula"))
            if not employee.is_actived:
                raise EmployeeDesactivedException("Trabajador no encontrado o no registrado.")
            current_work_center = self.cleaned_data.get("entrypoint").work_center
            print(f"Workcenter: ", employee.department.work_center, current_work_center, self.cleaned_data.get("entrypoint").allow_clocking_from_another_workcenter)
            if employee.department.work_center != current_work_center and not self.cleaned_data.get("entrypoint").allow_clocking_from_another_workcenter:
                raise EmployeeDoenstBelongsToThisWorkCenterException("El trabajador no pertenece a este centro")
        except ObjectDoesNotExist as e:
            log.exception(e)
            return None
        
        print("employee", employee, employee.__class__)
        return DailyChecks.objects.checking_user(employee, entrypoint=self.cleaned_data.get("entrypoint", None))
    

class CheckingObservationModelForm(forms.ModelForm):
    employer = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_actived=True),
        label="Trabajador",
        required=False,
        initial=None
    )

    
    person = forms.ModelChoiceField(
        queryset=Person.objects.filter(is_disabled=False),
        label="Trabajador (Pelado y descabezado)",
        required=False,
        initial=None
    )
    class Meta:
        model = DailyCalendarObservation
        exclude = (
            "created", 
            "modified"
        )



class DailyChecksProxyModelAdminForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_actived=True),
        label="Trabajador",
        required=False,
        initial=None,
        widget=forms.Select(attrs={
            "class": "border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 rounded-default shadow-xs text-font-default-light text-sm focus:outline-2 focus:-outline-offset-2 focus:outline-primary-600 group-[.errors]:border-red-600 focus:group-[.errors]:outline-red-600 dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:group-[.errors]:border-red-500 dark:focus:group-[.errors]:outline-red-500 dark:scheme-dark group-[.primary]:border-transparent px-3 py-2 w-full pr-8! max-w-2xl appearance-none truncate"
        })
    )

    
    person = forms.ModelChoiceField(
        queryset=Person.objects.filter(is_disabled=False),
        label="Trabajador (Pelado y descabezado)",
        required=False,
        initial=None,
        widget=forms.Select(attrs={
            "class": "border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 rounded-default shadow-xs text-font-default-light text-sm focus:outline-2 focus:-outline-offset-2 focus:outline-primary-600 group-[.errors]:border-red-600 focus:group-[.errors]:outline-red-600 dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark dark:group-[.errors]:border-red-500 dark:focus:group-[.errors]:outline-red-500 dark:scheme-dark group-[.primary]:border-transparent px-3 py-2 w-full pr-8! max-w-2xl appearance-none truncate"
        })
    )
    class Meta:
        model = DailyChecksProxyModelAdmin
        exclude = (
            "created", 
            "modified"
        )