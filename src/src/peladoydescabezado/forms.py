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
    names = forms.ChoiceField(
        label="Mesa",
        choices=[],
    )

    class Meta:
        model = Person
        fields = (
            "names", "lastnames", "identity",
        )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        from src.peladoydescabezado.models import Table
        from src.peladoydescabezado.utils import get_consecutive_code

        if 'names' in self.fields:
            self.fields['names'].choices = [
                (t.description, t.description)
                for t in Table.objects.filter(is_active=True)
            ]

        if 'lastnames' in self.fields:
            self.fields['lastnames'].label = "Código consecutivo"

        if 'identity' in self.fields:
            self.fields['identity'].label = "Consecutivo"

        # Precargar valores solo en creación (sin instancia guardada)
        if not self.instance.pk:
            user = self.request.user if self.request else None
            consecutive = get_consecutive_code(self.instance, user=user)
            if 'lastnames' in self.fields:
                self.fields['lastnames'].initial = consecutive
            if 'identity' in self.fields:
                self.fields['identity'].initial = int(consecutive)

    def clean(self):
        data = super().clean()
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
