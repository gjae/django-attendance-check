import logging
from pathlib import Path
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.core.files.storage import default_storage
import qrcode

from src.employees.models import Employee, Transfer
from src.peladoydescabezado.models import Person

@receiver(post_save, sender=Employee)
def on_create_employeer_record(sender, instance: Employee, created: bool, *args, **kwargs):
    QR_FOLDER_PATH = "/app/src/media/pictures/qrs"
    path = Path(QR_FOLDER_PATH)
    qr_file_name = f"{instance.cedula}.png"
    
    if instance.cedula == 0:
        return False
    
    if not path.exists():
        path.mkdir(parents=True)

    path = path.joinpath(qr_file_name)
    if path.is_file() :
        return False
    
    qr = qrcode.make(f"{instance.cedula}")
    qr.save(str(path))

@receiver(post_save, sender=Person)
def on_create_pelado_person_record(sender, instance: Person, created: bool, *args, **kwargs):
    QR_FOLDER_PATH = "/app/src/media/pictures/qrs"
    path = Path(QR_FOLDER_PATH)
    qr_file_name = f"{instance.cedula}.png"
    
    if instance.cedula == 0:
        return False
    
    if not path.exists():
        path.mkdir(parents=True)

    path = path.joinpath(qr_file_name)
    if path.is_file() :
        return False
    
    qr = qrcode.make(f"{instance.cedula}")
    qr.save(str(path))

@receiver(pre_save, sender=Transfer)
def on_employee_pre_transfer(sender, instance: Transfer, *args, **kwargs):
    if not hasattr(instance, "id") or instance.id is None:
        employer = instance.employee
        instance.from_department = employer.department

@receiver(post_save, sender=Transfer)
def on_employee_transfered(sender, instance: Transfer, created: bool, *args, **kwargs):
    """
    Cuando un empleado es movido desde un departamento a otro
    este signal se encarga de hacer el movimiento en la base de datos
    """

    LOG = logging.getLogger(__name__)
    LOG.info("Se esta realizando la transferencia entre departamento para un usuario")
    if not created:
        LOG.info("La transferencia fue modificada")
        return None
    

    empl: Employee = instance.employee
    empl.department = instance.to_department
    empl.save()

    LOG.info(f"El empleado {empl} fue movido desde el departamento {instance.from_department} al departamento {instance.to_department}")