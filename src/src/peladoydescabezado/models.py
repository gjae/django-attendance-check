from collections import OrderedDict
from django.db import models
from model_utils.models import TimeStampedModel
from model_utils import Choices

from src.settings.models import Department
from src.employees.models import EmployeePosition

CATEGORIES = Choices(
    (0, "ppv", "PPV"),
    (1, "pud", "PUD"),
    (2, "pyd", "PYD"),
    (3, "desc", "Descabezado"),
)


TURNS = Choices(
    (0, "morning", "Diurno"),
    (1, "night", "Nocturno"),
)

TURNS_TIME_RANGES = OrderedDict()
TURNS_TIME_RANGES["morning"] = ("8:00", "16:00")
TURNS_TIME_RANGES["night"] = ("6:00", "02:00")

# Create your models here.
class Person(TimeStampedModel):
    names = models.CharField(
        "Nombres",
        max_length=150
    )

    lastnames = models.CharField(
        "Apellidos",
        max_length=150
    )

    identity = models.PositiveIntegerField(
        "Cédula",
        db_index=True,
        unique=True
    )

    is_disabled = models.BooleanField(
        "Personal activo",
        default=False
    )

    identity_pic = models.ImageField(
        "Foto de la cédula o pasaporte",
        upload_to="peladoydescabezado/"
    )

    phone = models.CharField(
        "Teléfono",
        blank=True,
        default=""
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        verbose_name="Departamento"
    )

    position = models.ForeignKey(
        EmployeePosition,
        on_delete=models.SET_NULL,
        default=None,
        null=True,
        verbose_name="Cargo"
    )
    address = models.TextField(
        "Dirección",
        blank=True,
        default=""
    )

    personal_pic =  models.ImageField(
        "Foto",
        upload_to="peladoydescabezado/photos/",
        null=True,
        default=None
    )

    daily_basket = models.PositiveIntegerField(
        "Número diario de canastas",
        default=1
    )

    class Meta:
        verbose_name_plural = "Personal"
        verbose_name = "Trabajador"


    def __str__(self):
        return f"{self.names} {self.lastnames}"


class Table(TimeStampedModel):
    description = models.CharField(
        "Descripción de la mesa",
        max_length=50
    )

    max_workers = models.PositiveIntegerField(
        "Número máximo de trabajadores",
        default=1
    )

    category = models.SmallIntegerField(
        "Categoría de la mesa",
        choices=CATEGORIES
    )

    is_active = models.BooleanField(
        "Mesa activa",
        default=True
    )

    archived_at = models.DateTimeField(
        "Mesa archivada",
        null=True,
        default=None
    )

    class Meta:
        verbose_name_plural = "Mesas"
        verbose_name = "Mesa"


    def __str__(self):
        return f"{self.get_category_display()} - {self.description}"


class BasketProduction(TimeStampedModel):
    table = models.ForeignKey(
        Table,
        on_delete=models.SET_DEFAULT,
        related_name="baskets",
        null=True,
        default=None,
        verbose_name="Mesa"
    )

    worker = models.ForeignKey(
        Person,
        on_delete=models.RESTRICT,
        related_name="product_baskets",
        verbose_name="Trabajador"
    )

    weight = models.FloatField(
        "Total pesado",
        default=0.0,
        help_text="En  formato decimal: 0.5 equivale a 500Gr de producto"
    )

    turn = models.SmallIntegerField(
        "Categoría de la mesa",
        choices=TURNS
    )


    cost = models.DecimalField(
        "Costo por kilo",
        decimal_places=2,
        max_digits=12,
        default=0.00
    )

    total =  models.DecimalField(
        "Total generado",
        decimal_places=2,
        max_digits=12,
        default=0.00
    )

    class Meta:
        verbose_name_plural = "Cestas"
        verbose_name = "Cesta"

    def __str__(self):
        return f"{self.table.get_category_display()} // {self.worker}"


    
