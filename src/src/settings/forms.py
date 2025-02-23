from django import forms
from src.settings.models import ClientConfig, WorkCenter, CarnetModels


class ClientConfigModelForm(forms.ModelForm):

    class Meta:
        model = ClientConfig
        fields = ["description", "client_ip", "note", "allow_qr_clocking", "allow_clocking_from_another_workcenter", "work_center"]
        help_texts = {
            "client_ip": "Formato de la IP debe ser IPv4 (Ejemplo: 192.168.0.1)",
            "note": "Opcional: agregue una observación que pueda interesar recordar"
        }
    

class WorkCenterCreateForm(forms.ModelForm):
    class Meta:
        model = WorkCenter
        exclude = ["is_removed", "allow_clocking_from_another_workcenter"]


class CarnetModelCreateForm(forms.ModelForm):
    class Meta:
        model = CarnetModels
        fields = (
            "modelo",
            "front_path"
        )