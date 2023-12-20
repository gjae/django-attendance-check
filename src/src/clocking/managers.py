import math
from collections import deque
from datetime import timedelta
from django.utils import timezone
from django.db import models
from .exceptions import CheckingTooRecentException


class ClockingManager(models.Manager):

    def get_or_create_clocking_day(self):
        """
        Verifica que la fecha actual ha sido registrada en el calendario del sistema
        para realizar los checkeos, si la fecha actual no ha sido registrada, será registrada
        y se retornara la referencia
        """
        
        today = timezone.now()
        current_date, _ = self.get_or_create(date_day=today.date())

        return current_date


class CheckingManager(models.Manager):

    def checking_user(self, employee):
        """
        Realiza un check para el usuario para el día actual. Si el usuario
        tiene una entrada en el día actual entonces solo marca una salida

        Por día de calendario solo se puede tener máximo una entrada y una salida

        si el día anterior no tuvo salida y/o entrada, igual será marcado el día 
        actual e ignorará el anterior
        """

        from src.clocking.models import DailyCalendar, DailyChecks
        
        daily = DailyCalendar.objects.get_or_create_clocking_day()
        
        employee_calendar = DailyChecks.objects.filter(employee=employee, daily=daily)

        if not employee_calendar.exists():
            return DailyChecks.objects.create(employee=employee, daily=daily)
        
        elif employee_calendar.exists() and employee_calendar.first().checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada:
            checking = employee_calendar.first()
            checking_timeout = checking.checking_time + timedelta(minutes=3)

            # Si el tiempo en que el usuario ha realizado el chequeo es menor a 3 minutos
            # no permite que se realice un nuevo chequeo hasta pasados esos 3 minutos
            if timezone.now() <= checking_timeout:
                raise CheckingTooRecentException()
            

            return DailyChecks.objects.create(employee=employee, daily=daily, checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida)


        return employee_calendar.first()
    
    def _build_report_object(self, entry, out = None, total_hours = 0, use_for_database = False):
        obj = {
            "created": entry.daily.date_day,
            "employer": entry.employee,
            "total_hours": 0,
            "start_at": entry.checking_time.strftime("%d/%m/%Y %I:%M %p") if not use_for_database else entry.checking_time,
            "end_at": "SIN MARCAR" if out is None else out.checking_time.strftime("%d/%m/%Y %I:%M %p"),
            "abs_total_hours": total_hours
        }

        if out is not None and use_for_database:
            obj["end_at"] = out.checking_time
        elif out is None and use_for_database:
            obj["end_at"] = None

        return obj

    
    def report_by_employee(self, user_id = None, from_date = None, until_date = None, use_for_database = False, department = None):
        from src.clocking.models import DailyChecks
        new_data = (
            self
            .filter(daily__date_day__range=[
                from_date, 
                until_date
            ])
            .select_related("employee", "employee__position")
            .order_by("id", "employee_id")
        )
        if user_id is not None:
            new_data = new_data.filter(employee_id=user_id)
        if department is not None:
            new_data = new_data.filter(employee__department_id=department)

        divided_by_user = {}
        data_pdf = []
        pdf_deque = deque()
        total_hours_acumulateds = 0

        for data in new_data:
            if data.employee_id not in divided_by_user:
                divided_by_user[data.employee_id] = []
            divided_by_user[data.employee_id].append(data)

        for user_data in divided_by_user.keys():
            datas = divided_by_user[user_data]
            stack = list()
            if len(datas) == 1:
                report = datas[0]
                if department is not None:
                    pdf_deque.append(self._build_report_object(report, use_for_database=use_for_database))
                else:
                    data_pdf.append(self._build_report_object(report, use_for_database=use_for_database))

            for report in datas:
                if len(stack) == 0 and report.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada:
                    stack.append(report)
                elif len(stack) > 0 and report.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada:
                    last_element = stack.pop()
                    if last_element.daily_id != report.daily_id:
                        data_pdf.append(self._build_report_object(report, use_for_database=use_for_database))
                elif len(stack) > 0 and report.checking_type == DailyChecks.CHECK_STATUS_CHOISE.salida:
                    last_element = stack.pop()
                    total_hours = (report.checking_time - last_element.checking_time).total_seconds() / 60 / 60
                    total_hours_acumulateds += total_hours
                    if department is not None:
                        pdf_deque.append(self._build_report_object(last_element, report, math.ceil(total_hours), use_for_database=use_for_database))
                    else:
                        data_pdf.append(self._build_report_object(last_element, report, math.ceil(total_hours), use_for_database=use_for_database))
           

            if len(stack) == 1:
                report = stack.pop()
                if department is not None:
                    pdf_deque.append(self._build_report_object(report, use_for_database=use_for_database))
                else:
                    data_pdf.append(self._build_report_object(report, use_for_database=use_for_database))
                


        if department is not None:
            users = {}
            total_hours_acumulateds = 0
            while pdf_deque:
                element = pdf_deque.popleft()
                total_hours_acumulateds += element["abs_total_hours"]
                if element["employer"].id not in users:
                    users[element["employer"].id] = element
                    continue
                users[element["employer"].id]["abs_total_hours"] += element["abs_total_hours"]

            data_pdf = list(users.values())

        return data_pdf, math.ceil(total_hours_acumulateds)