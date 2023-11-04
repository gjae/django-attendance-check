from django import forms

class IdentificationModelForm(forms.ModelForm):
    class Meta:
        exclude = ["expire_at", "emited_at"]