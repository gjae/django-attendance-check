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


class CheckingManager(models.Manager):

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

        from src.clocking.models import DailyCalendar, DailyChecks
        


        # Consultar el ultimo registro de chequeo del usuario y verificar si el ultimo registro es una entrada
        # en caso de ser una entrada entonces se verifica si esa entrada fue hace menos de 24 horas, en ese 
        # caso se marca la salida correspondiente.
        # Si la ultima entrada fue hace mas de 24 horas entonces se marca una entrada del dia actual
        last_employer_check = DailyChecks.objects.filter(employee=employee).order_by("id").last()
        last_24_hours = datetime.now() - timedelta(hours=24)
        
        if last_employer_check is not None and last_employer_check.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada and (datetime.now() - last_employer_check.created).days < 1:
            self.raise_exception_is_checktimeout(last_employer_check)
            check_daily = last_employer_check.daily
            return DailyChecks.objects.create(employee=employee, daily=check_daily, checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida, entrypoint=entrypoint)



        daily = DailyCalendar.objects.get_or_create_clocking_day()
        employee_calendar = DailyChecks.objects.filter(employee=employee, daily=daily)

        if not employee_calendar.exists():
            return DailyChecks.objects.create(employee=employee, daily=daily, entrypoint=entrypoint)
        
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
            

            return DailyChecks.objects.create(employee=employee, daily=daily, checking_type=DailyChecks.CHECK_STATUS_CHOISE.salida, entrypoint=entrypoint)


        return employee_calendar.first()
    
    def _build_report_object(self, entry, out = None, total_hours = 0, use_for_database = False):
        obj = {
            "created": entry.daily.date_day,
            "employer": entry.employee,
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

    def report_by_department(self, *, department, from_date, until_date):
        from src.employees.models import Employee
        from src.clocking.models import DailyChecks
        logger = logging.getLogger("weasyprint")
        logger.addHandler(logging.NullHandler())
        logger.setLevel(40) 
        response = []
        days_checked_by_employer = {}
        hours_accumulateds = 0

        employers = (
            Employee
            .objects
            .select_related("position")
            .filter(department_id=department)
            .prefetch_related(
                Prefetch(
                    "daily_checks",
                    queryset=(
                        DailyChecks
                        .objects
                        .filter(
                            daily__date_day__range=[from_date, until_date]
                        )
                        .order_by("daily_id", "id")
                    ),
                    to_attr="checks"
                )
            )
        )

        for e in employers:
            total_hours = 0

            checks = list(self.list_chunks(e.checks, 2, total_checks=0))

            if e.cedula not in days_checked_by_employer:
                days_checked_by_employer[e.id] = len(checks)

            for idx, sublist in enumerate(checks):
                salida, entrada = sublist[1], sublist[0]
                if salida.id < entrada.id:
                    salida, entrada = salida, entrada
                # if e.id == 678:
                #    print(f"{salida} ({salida.daily_id}) - {entrada} ({entrada.daily_id}) = {round((salida.checking_time - entrada.checking_time).total_seconds() / 60 / 60, 2)}" )
                total_hours +=  round((salida.checking_time - entrada.checking_time).total_seconds() / 60 / 60, 2)

            hours_accumulateds += total_hours
            response.append({
                "created": e.checks[0].created.strftime("%d-%m-%Y") if len(e.checks) > 0 else "",
                "employer": e,
                "total_hours": total_hours,
                "start_at": "",
                "end_at": "SIN MARCAR" ,
                "abs_total_hours": round(total_hours, 2),
                "daily_id": -1
            })

            

        return response, round(hours_accumulateds, 2), days_checked_by_employer

    
    def report_by_employee(self, user_id = None, from_date = None, until_date = None, use_for_database = False, department = None):
        from src.clocking.models import DailyChecks
        new_data = (
            self
            .filter(daily__date_day__range=[
                from_date, 
                until_date
            ])
            .select_related("employee", "employee__position")
            .order_by("daily__date_day", "employee_id")
        )
        if user_id is not None:
            new_data = new_data.filter(employee_id=user_id)
        if department is not None:
            new_data = new_data.filter(employee__department_id=department)

        print("DATA REPORTE", new_data)
        divided_by_user = {}
        data_pdf = []
        pdf_deque = deque()
        total_hours_acumulateds = 0
        total_days_by_user = {}

        for data in new_data:
            if data.employee_id not in divided_by_user:
                divided_by_user[data.employee_id] = []
            divided_by_user[data.employee_id].append(data)

        for t in divided_by_user.keys():
            total_days_by_user[t] = 0

        for user_data in divided_by_user.keys():
            datas = divided_by_user[user_data]
            stack = list()
            if len(datas) == 1:
                report = datas[0]
                if department is not None:
                    pdf_deque.append(self._build_report_object(report, use_for_database=use_for_database))
                else:
                    data_pdf.append(self._build_report_object(report, use_for_database=use_for_database))
            else:
                for report in datas:
                    if len(stack) == 0 and report.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada:
                        stack.append(report)
                    elif len(stack) > 0 and report.checking_type == DailyChecks.CHECK_STATUS_CHOISE.entrada:
                        last_element = stack.pop()
                        if last_element.daily_id != report.daily_id:
                            data_pdf.append(self._build_report_object(last_element, use_for_database=use_for_database))
                            stack.append(report)
                    elif len(stack) > 0 and report.checking_type == DailyChecks.CHECK_STATUS_CHOISE.salida:
                        total_days_by_user[user_data] = total_days_by_user[user_data] + 1
                        last_element = stack.pop()
                        total_hours = round((report.checking_time - last_element.checking_time).total_seconds() / 60 / 60, 2)
                        total_hours_acumulateds += round(total_hours, 2)
                        if department is not None:
                            pdf_deque.append(self._build_report_object(last_element, report, round(total_hours, 2), use_for_database=use_for_database))
                        else:
                            data_pdf.append(self._build_report_object(last_element, report, round(total_hours, 2), use_for_database=use_for_database))
            

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
                total_hours_acumulateds += round(element["abs_total_hours"], 2)
                if element["employer"].id not in users:
                    users[element["employer"].id] = element
                    continue
                users[element["employer"].id]["abs_total_hours"] += round(element["abs_total_hours"], 2)

            data_pdf = list(users.values())

        return data_pdf, round(total_hours_acumulateds, 2), total_days_by_user