"""
Admin amigable para el registro de AUDITLOG (django-auditlog).

Reemplaza el LogEntryAdmin default de la librería para que en la interfaz de
auditoría se muestren, tanto en la columna "Resource" como en el filtro
"Resource Type", los nombres amigables de usuario (verbose_name de cada
modelo, ej: "Procedencia", "Totalización de servicios") en lugar del nombre
técnico interno (ghostserviceload / ghostemployee).

Relación con otros archivos: se importa desde
src/src/dining_room/admin.py (cargado por admin autodiscover) y se apoya en
el registro de modelos en AUDITLOG hecho en src/src/dining_room/models.py.
"""

from django.apps import apps
from django.contrib import admin
from django.urls import NoReverseMatch, reverse as urlresolvers_reverse
from django.utils.html import format_html

from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from django.contrib.admin import SimpleListFilter


def friendly_content_type_name(content_type):
    """
    Calcula el nombre amigable de un content type a partir del verbose_name
    de su modelo.

    Parámetros:
        content_type (ContentType): content type a traducir.

    Retorna:
        str: verbose_name del modelo (ej: "Totalización de servicios") o el
        nombre técnico en su defecto (modelos no registrados/deprecados).
    """
    model = content_type.model_class()
    if model is None:
        return content_type.model

    return (
        model._meta.verbose_name
        if hasattr(model._meta, "verbose_name")
        else content_type.model
    )


class FriendlyResourceTypeFilter(SimpleListFilter):
    """
    Filtro "Resource Type" de AUDITLOG con etiquetas amigables.

    Sustituye al ResourceTypeFilter de django-auditlog, que desplegaba los
    ids técnicos de los content types (ej: "ghostserviceload").
    """

    title = "Resource Type"
    parameter_name = "resource_type"

    def lookups(self, request, model_admin):
        """
        Construye las opciones del filtro con nombres amigables.

        Parámetros:
            request (HttpRequest): petición actual.
            model_admin (ModelAdmin): admin de la vista (LogEntry).

        Retorna:
            list[tuple[str, str]]: pares (id del content type, nombre amigable).
        """
        qs = model_admin.get_queryset(request)
        type_ids = set(qs.values_list("content_type_id", flat=True))
        lookups = []
        for content_type in (
            ct for ct in self.content_types() if ct.id in type_ids
        ):
            lookups.append(
                (str(content_type.id), friendly_content_type_name(content_type))
            )
        return list(lookups)

    @staticmethod
    def content_types():
        """
        Lista los content types correspondientes a cada LogEntry del queryset.

        Parámetros:
            Ninguno.

        Retorna:
            list[ContentType]: content types ordenados por nombre amigable.
        """
        lookup = LogEntry.objects.values_list(
            "content_type_id", flat=True
        ).distinct()
        content_types = list(
            apps.get_model(
                "contenttypes", "ContentType"
            ).objects.filter(id__in=list(lookup))
        )
        content_types.sort(
            key=lambda ct: friendly_content_type_name(ct).lower()
        )
        return content_types

    def queryset(self, request, queryset):
        """
        Filtra los LogEntry por el content type seleccionado.

        Parámetros:
            request (HttpRequest): petición actual.
            queryset (QuerySet): LogEntry base filtrada.

        Retorna:
            QuerySet: LogEntry del tipo de recurso elegido.
        """
        if self.value() is None:
            return queryset
        return queryset.filter(content_type_id=self.value())


class FriendlyLogEntryAdmin(LogEntryAdmin):
    """
    Admin de LogEntry (AUDITLOG) con etiquetas de recurso amigables.

    Mantiene el comportamiento del LogEntryAdmin de django-auditlog pero
    cambiando la columna "Resource" para que muestre el verbose_name del
    modelo auditado y el filtro "Resource Type" use FriendlyResourceTypeFilter.
    """

    list_filter = ["action", FriendlyResourceTypeFilter]

    @admin.display(description="Resource")
    def resource_url(self, obj):
        """
        Link al registro auditado con etiqueta de recurso amigable.

        Parámetros:
            obj (LogEntry): entrada de auditoría.

        Retorna:
            str: HTML con el link "Procedencia - <registro>" o el repr crudo
            cuando la vista del recurso ya no existe.
        """
        content_type = obj.content_type
        viewname = f"admin:{content_type.app_label}_{content_type.model}_change"
        try:
            args = [obj.object_pk] if obj.object_id is None else [obj.object_id]
            link = urlresolvers_reverse(viewname, args=args)
        except NoReverseMatch:
            return obj.object_repr
        return format_html(
            "<a href='{}'>{} - {}</a>",
            link,
            friendly_content_type_name(content_type),
            obj.object_repr,
        )


# Reencola el registro default de la librería para conservar la pestaña bajo
# el mismo app y namespace del admin.
try:
    admin.site.unregister(LogEntry)
except admin.sites.NotRegistered:
    pass

admin.site.register(LogEntry, FriendlyLogEntryAdmin)
