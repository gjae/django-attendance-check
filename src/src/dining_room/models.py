from datetime import time
from datetime import date as date_cls
from django.db import models
from django.db.models import Sum, Q
from django.contrib.auth import get_user_model
from model_utils.models import TimeStampedModel, SoftDeletableModel

from src.employees.models import Employee
from src.indentities.models import Identity

from src.dining_room.managers import CheckDiningRoomManager
from src.peladoydescabezado.models import Person
from auditlog.registry import auditlog
# Create your models here.

class ConfDiningRoomManager(models.Manager):
    pass

class ConfDiningRoom(TimeStampedModel, SoftDeletableModel):
    check_name = models.CharField(
        "Beneficio"
    )

    start_time = models.TimeField(
        "Horario de inicio"
    )

    end_time = models.TimeField(
        "Hora maxima de chequeo"
    )

    date_start = models.DateTimeField(
        "Fecha desde que se aplica el horario",
        null=True,
        default=None
    )

    is_all_day = models.BooleanField(
        "Valido para todo el dia",
        help_text=(
            "Si esta opción está activada, este tipo de chequeo podra ser usada todo el día por lo tanto anula las horas limites pero además, será solo aplicada "
            "el día indicado en el campo -fecha desde que se aplica el horario- "
        ),
        default=False
    )

    is_active = models.DateTimeField(
        "Turno desactivado",
        null=True,
        default=None
    )

    removeds = ConfDiningRoomManager()

    class Meta:
        verbose_name = "Configuracíon de turno"
        verbose_name_plural = "Configuración de turnos de comedor"


    def __str__(self):
        return self.check_name

    def save(self, *args, **kwargs):
        if self.end_time == time(0,0):
            self.end_time = time(23, 59, 59)
        
        super(ConfDiningRoom, self).save(*args, **kwargs)


class DiningChecking(TimeStampedModel, SoftDeletableModel):
    conf_dining_room = models.ForeignKey(ConfDiningRoom, on_delete=models.CASCADE, related_name="checkings")
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE, null=True, default=None, related_name="dining_room_checkings")
    employer = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="dining_room_checkings", null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="dining_room_checkings", null=True)
    

    objects = CheckDiningRoomManager()

    class Meta:
        verbose_name = "Chequeo de comedor"
        verbose_name_plural = "Chequeos de comedor"

    @property
    def employer_object(self):
        if self.employer is not None:
            return self.employer

        return self.person


User = get_user_model()


class GhostEmployee(TimeStampedModel, SoftDeletableModel):
    """
    Registro de "trabajador fantasma" del comedor.

    Representa a invitados o personal de alta rotación que reciben el beneficio
    del comedor sin ser personal fijo de la empresa y sin llevar un registro de
    asistencia asociado. Su única función es servir de shortcut para la carga
    de servicios entregados, los cuales se controlan a través del modelo
    GhostServiceLoad (app dining_room).

    NO se relaciona con employees.Employee ni afecta los cálculos de asistencia
    del personal fijo.
    """

    name = models.CharField(
        "Nombre / procedencia",
        max_length=255,
        help_text=(
            "Nombre corto que identifica la procedencia del beneficio cargado "
            "(ej: 'Visita Casa Matriz')"
        ),
    )
    is_actived = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Procedencia"
        verbose_name_plural = "Procedencias"
        ordering = ["name"]

    def __str__(self):
        return self.name


class GhostServiceLoadManager(models.Manager):
    def actives(self):
        """
        Retorna el queryset base de cargas de servicios fantasma no eliminadas.

        Parámetros:
            Ninguno.

        Retorna:
            QuerySet: cargas activas (is_removed=False) ordenadas por fecha descendente.
        """
        return self.get_queryset().filter(is_removed=False)

    def register_load(
        self,
        *,
        service_type,
        quantity,
        loaded_by=None,
        date_day=None,
        note="",
    ):
        """
        Registra una carga de servicios entregados a trabajadores fantasma.

        La primera carga del día para un tipo de servicio se marca como carga
        original (is_errata=False); toda carga posterior del mismo día y tipo
        de servicio es una "errata" (is_errata=True). Las erratas SUMAN al total
        del día, nunca sobreescriben.

        Parámetros:
            service_type (ConfDiningRoom): tipo de servicio (configurable por la
                administración del sistema).
            quantity (int): cantidad de servicios entregados en esta carga.
            loaded_by (User | None): usuario responsable de la carga.
            date_day (date | None): día de la carga; por defecto hoy.
            note (str): nota opcional, útil para explicar la errata.

        Retorna:
            GhostServiceLoad: la carga registrada.
        """
        if date_day is None:
            date_day = date_cls.today()

        prior_exists = self.actives().filter(
            date_day=date_day, service_type=service_type
        ).exists()

        return self.create(
            date_day=date_day,
            service_type=service_type,
            quantity=quantity,
            is_errata=prior_exists,
            loaded_by=loaded_by,
            note=note,
        )

    def totals_for_date(self, date_day=None):
        """
        Totaliza los servicios fantasma agrupados por tipo de servicio.

        Parámetros:
            date_day (date | None): día a totalizar; por defecto hoy.

        Retorna:
            list[dict]: lista con {'service_name': str, 'total': int} por tipo
            de servicio con carga en el día. La suma incluye cargas originales
            y erratas (las erratas suman).
        """
        if date_day is None:
            date_day = date_cls.today()

        return list(
            self.actives()
            .filter(date_day=date_day, service_type__isnull=False)
            .values("service_type__check_name")
            .annotate(total=Sum("quantity"))
            .order_by("service_type__check_name")
        )

    def total_for(self, date_day=None, service_type=None):
        """
        Total de servicios fantasma para un día (y opcionalmente un tipo de servicio).

        Parámetros:
            date_day (date | None): día a totalizar; por defecto hoy.
            service_type (ConfDiningRoom | None): si se indica, filtra por ese
                tipo de servicio.

        Retorna:
            int: número total de servicios entregados a trabajadores fantasmas
            en el día indicado (incluye erratas).
        """
        filters = {"date_day": date_day if date_day is not None else date_cls.today()}
        if service_type is not None:
            filters["service_type"] = service_type

        total = self.actives().filter(**filters).aggregate(total=Sum("quantity"))
        return total["total"] or 0

    def erratas_for(self, date_day, service_type):
        """
        Lista las cargas registradas (original + erratas) para un día y servicio.

        Parámetros:
            date_day (date): día a consultar.
            service_type (ConfDiningRoom): tipo de servicio a consultar.

        Retorna:
            QuerySet: cargas ordenadas cronológicamente, la primera es la carga
            original y las restantes son erratas.
        """
        return (
            self.actives()
            .filter(date_day=date_day, service_type=service_type)
            .order_by("created")
        )


class GhostServiceLoad(TimeStampedModel, SoftDeletableModel):
    """
    Control de la cantidad de servicios entregados a "trabajadores fantasma".

    Lleva el registro de los días en los que se cargaron beneficios para
    trabajadores fantasma (GhostEmployee), por tipo de servicio
    (ConfDiningRoom) y por día. Un mismo día y tipo de servicio puede tener
    varias cargas: la primera es la carga original (is_errata=False) y las
    siguientes son "erratas" (is_errata=True) que SUMAN al total del día sin
    sobreescribirlo.

    No figura como asistencia de personal y por tanto no afecta los cálculos
    de asistencia del personal fijo; sus totales sí se suman a los reportes de
    servicios entregados por el comedor.
    """

    date_day = models.DateField(
        "Día de la carga",
        db_index=True,
        help_text="Formato: DD/MM/AAAA",
    )
    service_type = models.ForeignKey(
        ConfDiningRoom,
        on_delete=models.PROTECT,
        related_name="ghost_service_loads",
        verbose_name="Tipo de servicio",
        null=True,
        default=None,
    )
    quantity = models.PositiveIntegerField(
        "Cantidad de servicios entregados",
        default=0,
    )
    is_errata = models.BooleanField(
        "Es errata",
        default=False,
        editable=False,
        help_text=(
            "Las cargas posteriores a la primera de un mismo día y tipo de "
            "servicio se marcan como erratas y suman al total del día"
        ),
    )
    note = models.CharField(
        "Nota",
        max_length=255,
        blank=True,
        default="",
        help_text="Nota opcional (recomendada al cargar una errata)",
    )
    loaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="ghost_service_loads",
        verbose_name="Responsable de la carga",
    )

    objects = GhostServiceLoadManager()

    class Meta:
        verbose_name = "Totalización de servicios"
        verbose_name_plural = "Totalización de servicios"
        ordering = ["-date_day", "created"]

    def __str__(self):
        return (
            f"{self.date_day.strftime('%d/%m/%Y')} - "
            f"{self.service_type} - {self.quantity}"
        )

    def save(self, *args, **kwargs):
        """
        Guarda la carga determinando el flag de errata.

        Si is_errata no fue fijado previamente en la instancia, se calcula
        verificando si ya existen cargas activas para el mismo día y tipo de
        servicio: la primera carga es la original y las siguientes erratas.

        Parámetros:
            *args, **kwargs: argumentos estándar de Model.save().

        Retorna:
            None (delega en super().save()).
        """
        if self._state.adding and not self.is_errata:
            prior_exists = GhostServiceLoad.objects.actives().filter(
                date_day=self.date_day,
                service_type=self.service_type,
            ).exists()
            self.is_errata = prior_exists

        super().save(*args, **kwargs)


def register_auditlog():
    """
    Registra los modelos de comedor (procedencias y totalización de servicios)
    en django-auditlog y retorna la instancia del registro de auditlog.

    Solo GhostServiceLoad y GhostEmployee se auditan: las cargas deben quedar
    registradas como auditoría (actor vía AuditlogMiddleware, timestamps y
    cambios de campos como quantity, note, loaded_by).

    Parámetros:
        Ninguno.

    Retorna:
        auditlog.registry.AuditlogModelRegistry: registro de auditlog tras
        agregar los modelos.
    """
    auditlog.register(GhostEmployee)
    auditlog.register(GhostServiceLoad)
    return auditlog


register_auditlog()