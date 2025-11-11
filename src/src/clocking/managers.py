import math
from collections import deque
from datetime import timedelta, datetime
from django.utils import timezone
from django.db import models
from django.db.models import Q, Prefetch
from .exceptions import CheckingTooRecentException, CheckingOutputTooRecentException
import logging


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


class BaseCheckingManager(models.Manager):
    def get_model(self):
        from src.employees.models import Employee
        return Employee
    
    def get_daily_report_model(self):
        from src.clocking.models import DailyChecks
        return DailyChecks
    
    def get_related_name(self):
        return "employee"


class CheckingManager(BaseCheckingManager):

    def raise_exception_is_checktimeout(self, checking):
        print(f"Raise exception para {checking}")
        checking_timeout = checking.checking_time + timedelta(minutes=3)

        # Si el tiempo en que el usuario ha realizado el chequeo es menor a 3 minutos
        # no permite que se realice un nuevo chequeo hasta pasados esos 3 minutos
        if timezone.now() <= checking_timeout:
            print("CHECK TYPE", checking.checking_type)
            if checking.checking_type == 0:
                raise CheckingTooRecentException()
            else:
                raise CheckingOutputTooRecentException()


    def checking_user(self, employee, *, entrypoint = None):
        """
        Realiza un check para el usuario para el día actual. Si el usuario
        tiene una entrada en el día actual entonces solo marca una salida

        Por día de calendario solo se puede tener máximo una entrada y una salida

        si el día anterior no tuvo salida y/o entrada, igual será marcado el día 
        actual e ignorará el anterior
        """

        from src.clocking.models import DailyCalendar, DailyChecks, Employee
        from src.peladoydescabezado.models import Person
        


        # Consultar el ultimo registro de chequeo del usuario y verificar si el ultimo registro es una entrada
        # en caso de ser una entrada entonces se verifica si esa entrada fue hace menos de 24 horas, en ese 
        # caso se marca la salida correspondiente.
        # Si la ultima entrada fue hace mas de 24 horas entonces se marca una entrada del dia actual
        last_employer_check = None
        last_24_hours = datetime.now() - timedelta(hours=24)
        if isinstance(employee, Employee):
            last_employer_check = DailyChecks.objects.filter(Q(employee=employee)).order_by("id").last()
        elif isinstance(employee, Person):
            last_employer_check = DailyChecks.objects.filter(Q(person=employee)).order_by("id").last()
        
        if last_employer_check is not None and last_employer_check.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada and (datetime.now() - last_employer_check.created).days < 1:
            self.raise_exception_is_checktimeout(last_employer_check)
            check_daily = last_employer_check.daily
            if isinstance(employee, Employee):
                return DailyChecks.objects.create(employee=employee, daily=check_daily, checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida, entrypoint=entrypoint)
            elif isinstance(employee, Person):
                return DailyChecks.objects.create(person=employee, daily=check_daily, checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida, entrypoint=entrypoint)



        last_employer_check = None
        employee_calendar = None

        daily = DailyCalendar.objects.get_or_create_clocking_day()
        if isinstance(employee, Employee):
            employee_calendar = DailyChecks.objects.filter(employee=employee, daily=daily)
            last_employer_check = DailyChecks.objects.filter(employee=employee).order_by("id").last()
        elif isinstance(employee, Person):
            employee_calendar = DailyChecks.objects.filter(person=employee, daily=daily)
            last_employer_check = DailyChecks.objects.filter(person=employee).order_by("id").last()

        if last_employer_check is not None:
            self.raise_exception_is_checktimeout(last_employer_check)

        
        if not employee_calendar.exists():
            if isinstance(employee, Employee):
                return DailyChecks.objects.create(employee=employee, daily=daily, entrypoint=entrypoint)
            elif isinstance(employee, Person):
                return DailyChecks.objects.create(person=employee, daily=daily, entrypoint=entrypoint)
        
        if employee_calendar.exists():
            checking = employee_calendar.first()
            checking_timeout = checking.checking_time + timedelta(minutes=3)
            # Si el tiempo en que el usuario ha realizado el chequeo es menor a 3 minutos
            # no permite que se realice un nuevo chequeo hasta pasados esos 3 minutos
            if timezone.now() <= checking_timeout:
                if checking.checking_type == 0:
                    raise CheckingTooRecentException()
                else:
                    raise CheckingOutputTooRecentException()
        
        if employee_calendar.exists() and employee_calendar.first().checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada:
            checking = employee_calendar.first()
            self.raise_exception_is_checktimeout(checking)
            
            if isinstance(employee, Employee):
                return DailyChecks.objects.create(employee=employee, daily=daily, checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida, entrypoint=entrypoint)
            elif isinstance(employee, Person):
                return DailyChecks.objects.create(person=employee, daily=daily, checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida, entrypoint=entrypoint)



        return employee_calendar.first()
    
    def _build_report_object(self, entry, out = None, total_hours = 0, use_for_database = False):
        obj = {
            "created": entry.daily.date_day,
            "employer": entry.employee,
            "person": entry.person,
            "total_hours": 0,
            "start_at": entry.checking_time.strftime("%d/%m/%Y %I:%M %p") if not use_for_database else entry.checking_time,
            "end_at": "SIN MARCAR" if out is None else out.checking_time.strftime("%d/%m/%Y %I:%M %p"),
            "abs_total_hours": round(total_hours, 2),
            "daily_id": entry.daily_id
        }

        if out is not None and use_for_database:
            obj["end_at"] = out.checking_time
        elif out is None and use_for_database:
            obj["end_at"] = None

        return obj
    
    def list_chunks(self, l: list, n, *, total_checks = 0): 
        response = []

        for idx, check in enumerate(l.copy()):
            try:
                if check.daily_id == l[idx + 1].daily_id and check.checking_type != l[idx + 1].checking_type:
                    response.append(check)
                    response.append(l[idx + 1])
            except:
                pass


        for i in range(0, len(response), n):  
            yield response[i:i + n] 

    def report_by_department(self, *, department, from_date, until_date, is_simple = True):
        from src.clocking.reportering import AttendanceReport
        report = (
            AttendanceReport(
                from_date, 
                until_date, 
                related_name=self.get_related_name(), 
                department=department
            )
            .sort()
            .make(simple = is_simple)
        )
        return report

    
    def report_by_employee(self, user_id = None, from_date = None, until_date = None, use_for_database = False, department = None, is_employer_model = True):
        new_data = (
            self.get_daily_report_model().objects
            .filter(daily__date_day__range=[
                from_date, 
                until_date
            ])
            .select_related("employee", "employee__position", "person", "person__position")
            .order_by("daily__date_day", "employee_id", "person_id")
        )
        filters = {}
        print("Reporte actual")
            
        if user_id is not None:
            if is_employer_model:
                filters["employee_id"] = user_id
            else:
                filters["person_id"] = user_id
            new_data = new_data.filter(**filters)
        if department is not None:
            if is_employer_model:
                filters["employee__department_id"] = department
            else:
                filters["person__department_id"] = department

            new_data = new_data.filter(employee__department_id=department)

        divided_by_user = {}
        data_pdf = []
        pdf_deque = deque()
        total_hours_acumulateds = 0
        total_days_by_user = {}

        daily_report_pair = {}

        for data in new_data:
            if data.employee_id not in divided_by_user:
                divided_by_user[data.employee_id] = []
            divided_by_user[data.employee_id].append(data)

        for t in divided_by_user.keys():
            total_days_by_user[t] = 0

        for user_data in divided_by_user.keys():
            datas = divided_by_user[user_data]
            prev_report = None
            if len(datas) == 1:
                if department is not None:
                    pdf_deque.append(self._build_report_object(datas[0], use_for_database=use_for_database))
                else:
                    data_pdf.append(self._build_report_object(datas[0], use_for_database=use_for_database))
                continue
            
            for idx, report in enumerate(datas):
                print("Reporte ", report)
                if report.employee_id is not None and not report.employee.is_actived:
                    continue
                if report.person_id is not None and  report.person.is_disabled:
                    continue
                if prev_report is None:
                    prev_report = report.daily_id
                    
                if report.daily_id not in daily_report_pair:
                    daily_report_pair[report.daily_id] = []

                if report.daily_id != prev_report and len(daily_report_pair[prev_report]) == 1:
                    if department is not None:
                        pdf_deque.append(self._build_report_object(daily_report_pair[prev_report][0], use_for_database=use_for_database))
                    else:
                        data_pdf.append(self._build_report_object(daily_report_pair[prev_report][0], use_for_database=use_for_database))

                daily_report_pair[report.daily_id].append(report)
                if len(daily_report_pair[report.daily_id]) == 2:
                    entrada, salida = daily_report_pair[report.daily_id]
                    if entrada.checking_time < salida.checking_time:
                        entrada, salida = salida, entrada

                    total_hours = round((entrada.checking_time - salida.checking_time).total_seconds() / 60 / 60, 2)
                    total_hours_acumulateds += total_hours
                    if department is not None:
                        pdf_deque.append(self._build_report_object(salida, entrada, round(total_hours, 2), use_for_database=use_for_database))
                    else:
                        data_pdf.append(self._build_report_object(salida, entrada, round(total_hours, 2), use_for_database=use_for_database))
                
                prev_report = report.daily_id

            if prev_report is not None and len(daily_report_pair[prev_report]) == 1:
                if department is not None:
                    pdf_deque.append(self._build_report_object(daily_report_pair[prev_report][0], use_for_database=use_for_database))
                else:
                    data_pdf.append(self._build_report_object(daily_report_pair[prev_report][0], use_for_database=use_for_database))

                        
        if department is not None:
            users = {}
            total_hours_acumulateds = 0
            while pdf_deque:
                element = pdf_deque.popleft()
                total_hours_acumulateds += round(element["abs_total_hours"], 2)
                if element["employer"].id not in users:
                    users[element["employer"].id] = element
                    continue
                users[element["employer"].id]["abs_total_hours"] += round(element["abs_total_hours"], 2)

            data_pdf = list(users.values())

        return data_pdf, round(total_hours_acumulateds, 2), total_days_by_user