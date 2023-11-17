from typing import Optional
from django.db import models

class TimeReportManager(models.Manager):

    def filter_by_time(self, start_date,  end_date):
        return self.filter(created__range=[start_date, end_date]).select_related("employer")

    def report_by_worker(self, start_date,  end_date, employer_id: Optional[int] = None) -> tuple:
        """
        Retorna una tupla donde la posicion 0 contiene el queryset
        del reporte y la posicion 1 contiene el total de hora trabajado,
        la posicion 0 es un diccionario donde la clave es el ID del
        trabajador y el valor es el total de horas trabajadas
        """
        total_hours = 0
        data = self.filter_by_time(start_date, end_date)

        if employer_id is not None:
            data = data.filter(employer_id=employer_id)

        for record in data:
            total_hours  += record.abs_total_hours


        return data, total_hours
    

    def report_by_department(self, start_date,  end_date, department_id: Optional[int] = None):
        total_hours = 0
        data = self.filter_by_time(start_date, end_date)

        if department_id is not None:
            data = data.filter(employer__department_id=department_id)

        for record in data:
            total_hours  += record.abs_total_hours


        return data, total_hours
