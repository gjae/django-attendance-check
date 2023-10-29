from django import forms
from src.settings.models import ClientConfig


class ClientConfigModelForm(forms.ModelForm):

    class Meta:
        model = ClientConfig
        fields = ["description", "client_ip", "note"]
        help_texts = {
            "client_ip": "Formato de la IP debe ser IPv4 (Ejemplo: 192.168.0.1)",
            "note": "Opcional: agregue una observación que pueda interesar recordar"
        }
    