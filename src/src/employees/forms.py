from django import forms

from src.employees.models import Employee, EmployeePosition, Transfer
from src.settings.models import Department

class EmployerModelForm(forms.ModelForm):

    position = forms.ModelChoiceField(
        queryset=EmployeePosition.objects.all(),
        empty_label="Seleccione uno",
        label="Cargo",
        widget=forms.Select(attrs={
            "class": "border bg-white font-medium rounded-md shadow-sm text-gray-500 text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-400 dark:focus:border-primary-600 dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full pr-8 max-w-2xl appearance-none truncate"
        })
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.only_enableds(),
        empty_label="Seleccione uno",
        label="Departamento",
        widget=forms.Select(attrs={
            "class": "border bg-white font-medium rounded-md shadow-sm text-gray-500 text-sm focus:ring focus:ring-primary-300 focus:border-primary-600 focus:outline-none group-[.errors]:border-red-600 group-[.errors]:focus:ring-red-200 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-400 dark:focus:border-primary-600 dark:focus:ring-primary-700 dark:focus:ring-opacity-50 dark:group-[.errors]:border-red-500 dark:group-[.errors]:focus:ring-red-600/40 px-3 py-2 w-full pr-8 max-w-2xl appearance-none truncate"
        })
    )



    class Meta:
        exclude = ["created", ]
        model = Employee


class TransferModelForm(forms.ModelForm):
    class Meta:
        model = Transfer
        exclude = ["created", "modified", "from_department"]
        readonly_fields = [ ]
        widgets = {
            "user": forms.HiddenInput(),
            "from_department": forms.HiddenInput()
        }