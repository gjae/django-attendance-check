
from typing import Any
from django.db import transaction
from django.core.management.base import BaseCommand

from src.employees.models import Employee

class Command(BaseCommand):

    def handle(self, *args: Any, **options: Any):
        with transaction.atomic():
            employes = []
            for employer in  Employee.objects.all():
                name, last_name = employer.last_name, employer.name
                employer.last_name = last_name
                employer.name = name

                employes.append(employer)

            Employee.objects.bulk_update(employes, ["name", "last_name"])
