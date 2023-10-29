from pathlib import Path
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.files.storage import default_storage
import qrcode

from src.employees.models import Employee

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