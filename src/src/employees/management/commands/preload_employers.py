import csv
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from src.employees.models import Employee, EmployeePosition
from src.settings.models import Department


class Command(BaseCommand):

    def handle(self, *args, **options):
        files = [
            "/app/src/preloads/concepcion.csv",
            "/app/src/preloads/destajos.csv",
            "/app/src/preloads/fijos.csv",
            "/app/src/preloads/nuevos_ingresos.csv",
        ]
        departments = {}
        charges = {}

        with transaction.atomic():
            for file in files:
                with open(file, newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=",")
                    for row in reader:
                        department = row[3]
                        charge = row[2]
                        idcard = int(row[1].replace("V-", "").replace(".", ""))
                        name, last_name = row[0].split(", ")
                        if department not in departments:
                            departments[departments], _ = Department.objects.get_or_create(description=department)
                        if charge not in charges:
                            charges[charge], _ = EmployeePosition.objects.get_or_create(position=charge)

                        Employee.objects.get_or_create(
                            cedula=idcard,
                            defaults={
                                "name": name,
                                "last_name": last_name,
                                "position_id": charges[charge].id,
                                "department": departments[department].id
                            }
                        )
                        