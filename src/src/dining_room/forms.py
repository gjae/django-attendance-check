from django import forms

from .models import ConfDiningRoom

class ConfDiningRoomForm(forms.ModelForm):

    class Meta:
        model = ConfDiningRoom
        exclude = [
            "is_active",
            "is_all_day",
        ]