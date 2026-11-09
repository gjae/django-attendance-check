from django import forms
from django.utils import timezone

from src.settings.models import WorkCenter
from .models import ConfDiningRoom, GhostEmployee, GhostServiceLoad


def unfold_select_widget():
    """
    Construye un widget Select con las clases tailwind/unfold usadas por
    los selects del admin de comedor (borde base-200, shadow-xs, estados
    de foco y dark mode). Cada llamada retorna una instancia nueva para
    evitar compartir estado entre campos.

    Parámetros:
        Ninguno.

    Retorna:
        forms.Select: widget estilizado consistente con el admin.
    """
    return forms.Select(
        attrs={
            "class": (
                "border border-base-200 bg-white font-medium min-w-20 "
                "placeholder-base-400 rounded-default shadow-xs "
                "text-font-default-light text-sm focus:outline-2 "
                "focus:-outline-offset-2 focus:outline-primary-600 "
                "group-[.errors]:border-red-600 "
                "focus:group-[.errors]:outline-red-600 "
                "dark:bg-base-900 dark:border-base-700 "
                "dark:text-font-default-dark "
                "dark:group-[.errors]:border-red-500 "
                "dark:focus:group-[.errors]:outline-red-500 "
                "dark:scheme-dark group-[.primary]:border-transparent "
                "px-3 py-2 w-full pr-8! max-w-2xl truncate"
            ),
        }
    )


class ConfDiningRoomForm(forms.ModelForm):

    class Meta:
        model = ConfDiningRoom
        exclude = [
            "is_active",
            "is_all_day",
            "is_removed"
        ]


class GhostEmployeeForm(forms.ModelForm):
    """
    Formulario del admin de comedor para crear y gestionar Procedencias
    (GhostEmployee).

    Solo el nombre es obligatorio; la relación con Empresa (WorkCenter) es
    opcional para mantener la procedencia genérica: si se define, su
    totalización de servicios se suma al reporte por empresa, discriminada
    por tipo de beneficio. El flag is_removed no se muestra.
    """

    work_center = forms.ModelChoiceField(
        label="Empresa",
        required=False,
        queryset=WorkCenter.objects.filter(is_removed=False).order_by("name"),
        help_text=(
            "Empresa a la que corresponde la procedencia (opcional); si se "
            "define, sus servicios cargados se suman a la totalización del "
            "reporte por empresa, discriminados por tipo de beneficio"
        ),
        widget=unfold_select_widget(),
    )

    class Meta:
        model = GhostEmployee
        fields = ["name", "work_center"]
        exclude = ["is_removed"]


class GhostServiceLoadForm(forms.ModelForm):
    """
    Formulario del admin de comedor para registrar la cantidad de servicios
    entregados a los registrados bajo Procedencias (GhostServiceLoad).

    El responsable de la carga no se selecciona en el formulario: se asigna
    automáticamente al usuario con sesión activa (request.user) desde el
    ModelAdmin. La fecha debe cargarse en formato DD/MM/AAAA y no se permiten
    cargas con fechas futuras.
    """

    procedencia = forms.ModelChoiceField(
        label="Procedencia",
        queryset=GhostEmployee.objects.filter(is_removed=False).order_by("name"),
        help_text="Procedencia (registro con nombre) a la que corresponde la carga",
        widget=unfold_select_widget(),
    )

    date_day = forms.DateField(
        label="Día de la carga",
        input_formats=["%d/%m/%Y", "%Y-%m-%d"],
        widget=forms.DateInput(
            format="%d/%m/%Y",
            attrs={
                "name": "date_day",
                "id": "id_date_day",
                "autocomplete": "off",
                "placeholder": "DD/MM/AAAA",
                # Clases tailwind de unfold para mantener consistencia visual con
                # los demás inputs del admin (mismo estilo que los selects del
                # admin de clocking)
                "class": (
                    "border border-base-200 bg-white font-medium min-w-20 "
                    "placeholder-base-400 rounded-default shadow-xs "
                    "text-font-default-light text-sm focus:outline-2 "
                    "focus:-outline-offset-2 focus:outline-primary-600 "
                    "group-[.errors]:border-red-600 focus:group-[.errors]:outline-red-600 "
                    "dark:bg-base-900 dark:border-base-700 dark:text-font-default-dark "
                    "dark:group-[.errors]:border-red-500 dark:focus:group-[.errors]:outline-red-500 "
                    "dark:scheme-dark group-[.primary]:border-transparent px-3 py-2 w-full "
                    "pr-8! max-w-2xl truncate"
                ),
            },
        ),
    )

    service_type = forms.ModelChoiceField(
        label="Tipo de servicio",
        queryset=ConfDiningRoom.objects.filter(
            is_removed=False,
            is_active__isnull=True,
        ).order_by("check_name"),
        help_text="Solo se listan beneficios activos y no eliminados",
        widget=unfold_select_widget(),
    )

    class Meta:
        model = GhostServiceLoad
        fields = ["procedencia", "date_day", "service_type", "quantity", "note"]
        exclude = ["is_removed", "is_errata", "loaded_by"]

    def clean_date_day(self):
        """
        Valida que la fecha de la carga no sea futura.

        Parámetros:
            Ninguno (usa self.cleaned_data).

        Retorna:
            date: la fecha validada de la carga.

        Lanza:
            ValidationError: cuando la fecha indicada es posterior a hoy.
        """
        date_day = self.cleaned_data.get("date_day")

        try:
            today = timezone.localtime(timezone.now()).date()
        except (ValueError, TypeError):
            # USE_TZ=False: timezone.now() es naive y ya está en hora local
            today = timezone.now().date()

        if date_day and date_day > today:
            raise forms.ValidationError(
                "No se pueden registrar cargas con fechas futuras"
            )

        return date_day