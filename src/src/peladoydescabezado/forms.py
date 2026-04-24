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
            consecutive = get_consecutive_code(self.instance)
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


_SELECT_WIDGET_CLASS = (
    "border border-base-200 bg-white font-medium min-w-20 placeholder-base-400 "
    "rounded-default shadow-xs text-font-default-light text-sm focus:outline-2 "
    "focus:-outline-offset-2 focus:outline-primary-600 group-[.errors]:border-red-600 "
    "focus:group-[.errors]:outline-red-600 dark:bg-base-900 dark:border-base-700 "
    "dark:text-font-default-dark dark:group-[.errors]:border-red-500 "
    "dark:focus:group-[.errors]:outline-red-500 dark:scheme-dark "
    "group-[.primary]:border-transparent px-3 py-2 w-full pr-8! max-w-2xl "
    "appearance-none truncate"
)


class PersonDailyChecksProxyForm(forms.ModelForm):
    """
    Formulario para el admin de Asignar Chequeos (Personal P&D).
    Solo expone el campo `person`; el campo `employee` se excluye del formulario
    porque esta vista es exclusiva para trabajadores de Pelado y Descabezado.
    """

    person = forms.ModelChoiceField(
        queryset=Person.objects.filter(is_disabled=False).order_by(
            "names", "lastnames", "consecutive"
        ),
        label="Trabajador (Pelado y Descabezado)",
        required=True,
        widget=forms.Select(attrs={"class": _SELECT_WIDGET_CLASS}),
    )

    class Meta:
        model = DailyChecks
        fields = (
            "person",
            "daily",
            "checking_type",
            "checking_time",
            "entrypoint",
        )
