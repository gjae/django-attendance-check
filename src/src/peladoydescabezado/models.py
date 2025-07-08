from collections import OrderedDict
from django.db import models
from model_utils.models import TimeStampedModel
from model_utils import Choices
from django.contrib.auth import get_user_model

from src.employees.models import EmployeePosition
from src.settings.models import Department as BaseDepartment
from src.peladoydescabezado.managers import FarmManager, ControlManager, PersonManager, BasketProductionManager

CATEGORIES = Choices(
    (0, "ppv", "PPV"),
    (1, "pud", "PUD"),
    (2, "pyd", "PYD"),
    (3, "desc", "Descabezado"),
)


TURNS = Choices(
    (0, "morning", "Diurno"),
    (1, "night", "Nocturno"),
    (2, "evening", "Vespertino")
)

TURNS_TIME_RANGES = OrderedDict()
TURNS_TIME_RANGES["morning"] = ("8:00", "16:00")
TURNS_TIME_RANGES["night"] = ("6:00", "02:00")

User = get_user_model()

# Create your models here.
class Department(BaseDepartment):
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"



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
        upload_to="peladoydescabezado/",
        null=True,
        default=None
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

    is_actived = models.BooleanField(
        "Personal activado",
        default=True
    )

    objects = PersonManager()

    class Meta:
        verbose_name_plural = "Personal"
        verbose_name = "Trabajador"


    def __str__(self):
        return f"{self.names} {self.lastnames}"

    @property
    def picture(self):
        return self.personal_pic
    
    @property
    def name(self):
        return f"{self.names} {self.lastnames}"
    
    @property
    def lastname(self):
        return self.lastnames
    
    @property
    def cedula(self):
        return self.identity
    
    @property
    def allow_checking(self):
        return True
    
    def get_fullname(self):
        return self.__str__()
    
    @property
    def last_name(self):
        return self.lastnames
    
    @property
    def name(self):
        return self.names

    @property
    def is_birthday(self):
        return False

class Farm(TimeStampedModel):
    number = models.PositiveBigIntegerField(
        "Número de la granja",
        db_index=True,
        null=True,
        default=None
    )

    name = models.CharField(
        "Nombre de la granja",
        max_length=100,
        db_index=True
    )

    objects = FarmManager()

    class Meta:
        verbose_name = "Granja"
        verbose_name_plural = "Granjas"

    def __str__(self):
        return f"Granja: {self.name}"


class Pool(TimeStampedModel):
    number = models.PositiveBigIntegerField(
        "Número de la piscina",
        db_index=True,
        null=True,
        default=None
    )

    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="pools",
        verbose_name="Granja"
    )

    class Meta:
        verbose_name = "Piscina"
        verbose_name_plural = "Piscinas"

    def __str__(self):
        return f"Piscina: {self.number} ({self.farm.name})"


class Size(TimeStampedModel):
    description = models.CharField(
        "Talla",
        max_length=10
    )
    

    class Meta:
        verbose_name = "Talla"
        verbose_name_plural = "Tallas"


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

class Control(TimeStampedModel):
    code = models.CharField(
        "Código",
        max_length=50,
        db_index=True
    )

    date_upload = models.DateField(
        "Fecha de gestión"
    )

    turn = models.IntegerField(
        choices=TURNS,
        null=True,
        default=None
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="production_control_created",
        null=True,
        default=None
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="production_control_approved",
        null=True,
        default=None
    )

    checked_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="production_control_checked",
        null=True,
        default=None
    ) 

    objects = ControlManager()


class Weightness(TimeStampedModel):
    weight = models.CharField(
        "Denominación",
        max_length=60,
    )

    class Meta:
        verbose_name = "Talla"
        verbose_name_plural = "Tallas"

    def __str__(self):
        return self.weight

class ControlDetail(TimeStampedModel):
    control = models.ForeignKey(
        Control,
        related_name="details",
        on_delete=models.CASCADE
    )

    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="daily_control",
        null=True,
        default=None

    )

    pool = models.ForeignKey(
        Pool,
        on_delete=models.CASCADE,
        related_name="daily_control",
        null=True,
        default=None
    )
    
    total_weight_received = models.DecimalField(
        "Kilos de camarón recibido",
        decimal_places=2,
        max_digits=7,
        null=True,
        default=None
    )

    weightness = models.ManyToManyField(
        Weightness,
        related_name="control_details"
    )


class BasketProduction(TimeStampedModel):
    TOTALIZATION_METHOD = Choices(
        (0, "Por Cesta"),
        (1, "Por Kilo")
    )
    
    pool = models.ForeignKey(
        Pool,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="productions",
        verbose_name="Piscina"
    )

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
        on_delete=models.CASCADE,
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

    weight_totalization_method = models.SmallIntegerField(
        "Metodo de totalización",
        choices=TOTALIZATION_METHOD,
        default=0
    )

    control = models.ForeignKey(
        Control,
        on_delete=models.CASCADE,
        null=True,
        default=None,
        related_name="production"
    )

    saved_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="production_saveds",
        null=True,
        default=None
    )

    objects = BasketProductionManager()

    class Meta:
        verbose_name_plural = "Producción"
        verbose_name = "Producción"

    def __str__(self):
        return f"{self.table.get_category_display()} // {self.worker}"



class TableProxyModel(Table):
    class Meta:
        proxy = True
        verbose_name = "Gestión de peso"
        verbose_name_plural = "Gestion de pesaje"


class ReportProxyModel(Table):
    class Meta:
        proxy = True
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
        permissions = [
            ("can_generate_prod_reports", "Puede generar reporte de producción"),
            ("can_generate_assist_reports", "Puede generar reportes de asistencia")
        ]