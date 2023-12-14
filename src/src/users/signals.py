import os
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
import qrcode

User = get_user_model()

@receiver(post_save, sender=User)
def on_create_user_save_hers_qr(sender, instance: User, created, *args, **kwargs):
    if created:
        instance.is_staff = True
        instance.save()
