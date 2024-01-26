import csv
from datetime import datetime
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from src.employees.models import Employee, EmployeePosition
from src.settings.models import Department


class Command(BaseCommand):

    def handle(self, *args, **options):
        files = [
            "/app/src/preloads/concepcion.csv",
        ]
        departments = {}
        charges = {}

        with transaction.atomic():
            for file in files:
                with open(file, newline='') as csvfile:
                    reader = csv.reader(csvfile, delimiter=",")
                    for row in reader:
                        department = row[4]
                        charge = row[3]
                        idcard = int(row[2].replace("V", "").strip())
                        name, last_name = row[0], row[1]
                        if department not in departments:
                            departments[department], _ = Department.objects.get_or_create(name=department)
                        if charge not in charges:
                            charges[charge], _ = EmployeePosition.objects.get_or_create(position=charge)

                        Employee.objects.get_or_create(
                            cedula=idcard,
                            defaults={
                                "name": name.strip(),
                                "last_name": last_name.strip(),
                                "position_id": charges[charge].id,
                                "department_id": departments[department].id,
                                "birthday_at": datetime.strptime(row[6], "%d/%m/%Y"),
                                "date_entry_job": datetime.strptime(row[5], "%d/%m/%Y"),
                            }
                        )
                        