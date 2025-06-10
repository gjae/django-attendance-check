from datetime import time
from django.db import models
from model_utils.models import TimeStampedModel, SoftDeletableModel

from src.employees.models import Employee
from src.indentities.models import Identity

from src.dining_room.managers import CheckDiningRoomManager
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
    employer = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="dining_room_checkings")

    objects = CheckDiningRoomManager()

    class Meta:
        verbose_name = "Chequeo de comedor"
        verbose_name_plural = "Chequeos de comedor"

    