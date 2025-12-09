from src.clocking.models import DailyChecks
from typing import List
from dataclasses import dataclass
from django.db.models import (
    Window, F, Value, BooleanField, DateField, CharField, 
    IntegerField, FloatField, TimeField, Case, When, 
    ExpressionWrapper,
    Subquery,
    DateTimeField,
    Q
)
from django.db.models.functions import Lead, RowNumber, ExtractHour, ExtractMinute
from collections import defaultdict
from datetime import timedelta, datetime
from django.db import models
from django.db.models import Prefetch
from src.utils.date_utils import days_between_daterange

from src.employees.models import Employee
from src.peladoydescabezado.models import Person

@dataclass
class TimeRecord:
    start_time: datetime
    end_time: datetime
    total_hours: float
    day: object


class AttendanceReport:
    def __init__(self, from_date, until_date, related_name = "employee", department = None, include_unattendances = True, work_center=1):
        self.from_date = from_date
        self.until_date = until_date
        self.related_name = related_name
        self.department = department
        self.union_model = Employee if related_name == "employee" else Person
        self.unattendances = include_unattendances
        self.work_center = work_center

        self.name_field = "name" if related_name == "employee" else "names"
        self.lastname_field = "last_name" if related_name == "employee" else "lastnames"
        self.identification_field = "identity" if related_name != "employee" else "cedula"
        
        self.set_date_range = set(self.get_day_range(from_date, until_date))

        self.queryset = self.general_report(self.from_date, self.until_date)

    def get_related_name(self):
        return self.related_name

    def general_report(self, from_date, until_date):
        from src.clocking.models import DailyChecks
        related_name = self.get_related_name()
        
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date, "%Y-%m-%d")
        if isinstance(until_date, str):
            until_date = datetime.strptime(until_date, "%Y-%m-%d")
        
        date_range = days_between_daterange(from_date.date(), until_date.date())
        related_name = self.get_related_name() # Helper para obtener el nombre de la relación
        identification_field = self.identification_field

        # Se definen los campos a exportar para la UNION (el mismo orden es CRÍTICO)
        VALUE_FIELDS = (
            "day", "is_header", "uemployer","start_time", 
            "end_time", "total_hours", "uemployer_name", "uemployer_lastname",  "uemployer_cedula",  "row_number",
            "department_name", "uposition", "check_created", "current_department_id", "attendance_kind"
        )
        daily_union = None


        for day in date_range:
            data_query = None
            unattendances = None
            if self.unattendances:
                unattendances = (
                    self.union_model
                    .objects
                    .exclude(id__in=Subquery(
                        DailyChecks.objects
                        .filter(daily__date_day=day)
                        .values_list(f"{related_name}__id", flat=True)
                    ))
                    .filter(department__work_center_id=self.work_center)
                    .annotate(
                        attendance_kind=Value(1, output_field=IntegerField()),
                        current_department_id=F("department_id"),
                        row_number=Value(9999, output_field=IntegerField()),
                        next_check_time=Value(None, TimeField()),
                        next_daily_date=Value(None, DateField()),
                        check_created=F("created"),
                        department_name=F(f"department__name"),
                        is_header=Value(False, BooleanField()),
                        day=Value(day, output_field=DateTimeField()),
                        uposition=F(f"position__position"),
                        uemployer=F(f"id"),
                        uemployer_name=F(f"{self.name_field}"),
                        uemployer_lastname=F(f"{self.lastname_field}"),
                        uemployer_cedula=F(f"{identification_field}"),
                        start_time=Value(None, TimeField()),
                        # Solo usar como salida si es del mismo día
                        end_time=Value(None, TimeField()),
                        # Calcular horas solo si hay salida del mismo día
                        total_hours=Value(0, output_field=FloatField())
                    )
                    .values(*VALUE_FIELDS)
                )

                print(f"Union: {self.union_model.__class__} // {Employee.__class__} => {self.union_model.__class__ == Employee.__class__}")
                if self.union_model.__class__ == Employee.__class__:
                    unattendances = unattendances.filter(is_actived=True)

            data_query = (
                DailyChecks.objects
                .filter(daily__date_day=day)
                .filter(
                    Q(employee__isnull=False, employee__department__work_center_id=self.work_center)
                    | Q(person__isnull=False, person__department__work_center_id=self.work_center)
                )
                .select_related(self.get_related_name())
                .annotate(
                    # Numerar registros por persona y día
                    row_number=Window(
                        expression=RowNumber(),
                        partition_by=[F(f"{related_name}__id"), F("daily__date_day")],
                        order_by=[F("daily__date_day").asc(),  F("checking_time").asc()]
                    ),
                    # Obtener el siguiente registro de la misma persona y mismo día
                    next_check_time=Window(
                        expression=Lead("checking_time"),
                        partition_by=[F(f"{related_name}__id"), F("daily__date_day")],
                        order_by=F("checking_time").asc()
                    ),
                    next_daily_date=Window(
                        expression=Lead("daily__date_day"),
                        partition_by=[F(f"{related_name}__id")],
                        order_by=F("checking_time").asc()
                    )
                )
                .annotate(
                    attendance_kind=Value(0, output_field=IntegerField()),
                    current_department_id=F(f"{related_name}__department_id"),
                    check_created=F("created"),
                    department_name=F(f"{related_name}__department__name"),
                    is_header=Value(False, BooleanField()),
                    day=F("daily__date_day"),
                    uposition=F(f"{related_name}__position__position"),
                    uemployer=F(f"{related_name}__id"),
                    uemployer_name=F(f"{related_name}__{self.name_field}"),
                    uemployer_lastname=F(f"{related_name}__{self.lastname_field}"),
                    uemployer_cedula=F(f"{related_name}__{identification_field}"),
                    start_time=F("checking_time"),
                    # Solo usar como salida si es del mismo día
                    end_time=Case(
                        When(
                            next_daily_date=F("daily__date_day"),  # Mismo día
                            then=F("next_check_time")
                        ),
                        default=Value(None),
                        output_field=models.DateTimeField()
                    ),
                    # Calcular horas solo si hay salida del mismo día
                    total_hours=Case(
                        When(
                            next_daily_date=F("daily__date_day"),
                            then=ExpressionWrapper(
                                (ExtractHour(F("next_check_time") - F("checking_time")) * 60 +
                                ExtractMinute(F("next_check_time") - F("checking_time"))) / 60.0,
                                output_field=FloatField()
                            )
                        ),
                        default=Value(0.0),
                        output_field=FloatField()
                    )
                )
                .order_by("day", "uemployer_cedula", "uemployer_lastname", "uemployer_name")
                .values(*VALUE_FIELDS)
            )

            if self.department is not None:
                if self.unattendances:
                    unattendances = unattendances.filter(current_department_id=self.department)
                data_query = data_query.filter(current_department_id=self.department)
            # Unir Marcador y Datos para el Día (asegurando que el marcador sea el primer registro)
            if daily_union is None:
                daily_union = data_query.union(unattendances) if self.unattendances else data_query
            else:
                daily_union = daily_union.union(data_query.union(unattendances)) if self.unattendances else daily_union.union(data_query)
        

        return daily_union


    def get_queryset(self):
        return self.queryset
    
    def get_day_range(self, start_date: str, end_date: str, date_format: str = "%Y-%m-%d") -> List[str]:
        """
        Genera una lista ordenada con todos los días entre dos fechas.
        
        Args:
            start_date (str): Fecha de inicio en formato string
            end_date (str): Fecha fin en formato string
            date_format (str): Formato de las fechas (por defecto: YYYY-MM-DD)
            
        Returns:
            List[str]: Lista de fechas en formato string ordenadas cronológicamente
            
        Raises:
            ValueError: Si las fechas no están en el formato correcto o si start_date > end_date
        """
        # Convertir strings a objetos datetime
        start = datetime.strptime(start_date, date_format) if isinstance(start_date, str) else start_date
        end = datetime.strptime(end_date, date_format) if isinstance(end_date, str) else end_date
        
        # Validar que start_date no sea mayor que end_date
        if start > end:
            raise ValueError("start_date no puede ser mayor que end_date")
        
        # Generar la lista de días
        days_list = []
        current_date = start
        
        while current_date <= end:
            days_list.append(current_date.date())
            current_date += timedelta(days=1)
        
        return days_list
    
    def group_by_date(self):
        new_data = defaultdict(lambda: [])
        row_counter = 0
        for data in self.queryset:
            row_counter += 1
            user_data = {
                "cedula": data["uemployer_cedula"],
                "name": data["uemployer_name"],
                "last_name": data["uemployer_lastname"],
                "department": data["department_name"],
                "id": data["uemployer"],
                "position": {
                    "position": data["uposition"]
                }
            }
            new_data[data["day"]].append({
                "id": data["uemployer"],
                "created": data["check_created"].strftime("%d-%m-%Y"),
                "employer": user_data,
                "person": user_data,
                "total_hours": round(data["total_hours"], 2),
                "start_at": data["start_time"],
                "end_at": data["end_time"] ,
                "abs_total_hours": round(data["total_hours"], 2),
                "daily_id": -1,
                "row": row_counter
            })

        return new_data
    
    def _complete_week_days(self, dates: List[TimeRecord]) -> List[TimeRecord]:
        result = set([t.day for t in dates]).symmetric_difference(self.set_date_range)
        return dates + [TimeRecord(start_time=None, end_time=None, total_hours=0, day=d if not isinstance(d, str) else datetime.strptime(d, "%Y-%m-%d")) for d in result]
    

    def group_by_user(self):
        new_data = defaultdict(lambda: dict())
        row_counter = 0
        for data in self.queryset:
            real_row_counter = row_counter
            if "row" not in new_data[data["uemployer"]]:
                row_counter += 1
            else:
                row_counter = new_data[data["uemployer"]]["row"]

            new_data[data["uemployer"]] = {
                "row": real_row_counter,
                "row_number": real_row_counter,
                "cedula": data["uemployer_cedula"],
                "name": data["uemployer_name"],
                "last_name": data["uemployer_lastname"],
                "department": data["department_name"],
                "id": data["uemployer"],
                "position": {
                    "position": data["uposition"]
                },
                "dates": new_data[data["uemployer"]].get("dates", []) + [
                    TimeRecord(
                        start_time=data["start_time"], 
                        end_time=data["end_time"], 
                        total_hours=data["total_hours"],
                        day=data["day"]
                    )
                ],
            }
        for user_id in new_data:
            new_data[user_id]["dates"] = sorted(self._complete_week_days(new_data[user_id]["dates"]), key=lambda x: x.day.date() if isinstance(x.day, datetime) else x.day)

        return new_data


    def unique_by_user(self):
        new_data = []
        seen_ids = set()
        for data in self.queryset:
            if data["uemployer"] not in seen_ids:
                seen_ids.add(data["uemployer"])
                new_data.append(data)

        self.queryset = new_data
        return self


    def sort(self, datail = False):
        data = []
        if datail:
            data = list(self.queryset) if not isinstance(self.queryset, list) else self.queryset
        else:
            data = list(
                filter(lambda d: d["row_number"] % 2 == 1, self.queryset)
            )

        data.sort(key=lambda x: (
            x["day"], 
            x["department_name"] if x["department_name"] is not None else "",
            x["uemployer_lastname"], 
            x["uemployer_name"],
            x["uemployer_cedula"], 
        ))
        
        self.queryset = data
        return self
    

    def _simple_report(self, flat = False):
        response = []
        total_hours = 0.00
        counters = defaultdict(lambda: 0)
        for data in self.queryset:
            total_hours += data["total_hours"]
            user_data = {
                "cedula": data["uemployer_cedula"],
                "name": data["uemployer_name"],
                "last_name": data["uemployer_lastname"],
                "department": data["department_name"],
                "id": data["uemployer"],
                "position": {
                    "position": data["uposition"]
                }
            }
            response.append({
                "id": data["uemployer"],
                "created": data["check_created"].strftime("%d-%m-%Y"),
                "employer": user_data,
                "person": user_data,
                "total_hours": round(data["total_hours"], 2),
                "start_at": "",
                "end_at": "SIN MARCAR" ,
                "abs_total_hours": round(data["total_hours"], 2),
                "daily_id": -1
            })
            if data["attendance_kind"] == 0:
                counters[data["uemployer"]] += 1

        
        return AttendanceReport.flat(response), round(total_hours, 2), counters

    @staticmethod
    def flat(report):
        response = defaultdict(lambda: {"total_hours": 0})
        current_row = 0
        for data in report:
            current_row += 1
            response[data["id"]] = {
                **response[data["id"]],
                **data,
                "total_hours": response[data["id"]]["total_hours"] + data["total_hours"],
                "abs_total_hours": response[data["id"]]["total_hours"] + data["total_hours"],
                "row_number": current_row,
                "row": current_row
            }

        return list(response.values())

    def make(self, simple = False):
        if simple:
            return self._simple_report()
        
        return self.queryset



