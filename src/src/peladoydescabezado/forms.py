from django import forms

from src.employees.models import Employee
from src.clocking.models import DailyChecks
from src.peladoydescabezado.models import (
    Farm,
    Pool,
    Person,
    Weightness,
    BasketProduction,
)
from .exceptions import (
    WorkerIsNotPresentException,
)


class FarmModelForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = (
            "name",
        )


class PoolModelForm(forms.ModelForm):
    class Meta:
        model = Pool
        fields = (
            "number",
            "farm"
        )


class PersonalModelForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = (
            "names", "lastnames", "identity", "personal_pic", "department", "position",
        )

    def clean(self):
        data = super().clean()
        cedula = data.get("identity")
        exists = Employee.objects.filter(cedula=int(cedula)).filter(is_actived=True)

        if exists.exists():
            raise forms.ValidationError(
                f"Ya existe un trabajador registrado con la cédula {cedula}"
            )
        
        return data


class WeightnessModelForm(forms.ModelForm):
    class Meta:
        model = Weightness
        fields = [
            "weight",
        ]



class LoadWeightForm(forms.ModelForm):

    class Meta:
        model = BasketProduction
        fields = (
            "table",
            "worker",
            "weight",
            "turn",
            "control",
            "saved_by",
        )
