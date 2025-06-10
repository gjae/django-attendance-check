from django import forms

from src.peladoydescabezado.models import (
    Farm,
    Pool
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