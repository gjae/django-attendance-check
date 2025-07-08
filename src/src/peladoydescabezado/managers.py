from decimal import Decimal
from datetime import datetime, timedelta
from collections import defaultdict
from django.db.models import Manager, Prefetch, Window, Sum, Q, Count, Subquery, OuterRef, Value, F
from django.db.models.functions import Coalesce, TruncDate
from django.db.models.functions import RowNumber
from src.employees.managers import BaseCheckingManager
from src.clocking.managers import CheckingManager as ClockingBaseCheckingManager

class FarmManager(Manager):

    def get_farms_with_pool_as_dict(self):
        farms = []

        for farm in self.get_queryset().prefetch_related(Prefetch("pools", to_attr="pools_array")):
            farms.append({
                "id": farm.id,
                "name": farm.name,
                "pools": [{
                    "id": pool.id,
                    "number": pool.number
                } for pool in farm.pools_array]
            })

        return farms
    

class ControlManager(Manager):

    def control_by_turn(self, user, load_turn = None, load_date = None):
        from src.peladoydescabezado.utils import get_current_turn
        TURN_INDEX = {"morning": 0, "night": 1}
        turn_id = 2
        if (current_turn := get_current_turn()) in TURN_INDEX:
            turn_id = TURN_INDEX[current_turn]

        turn_id = turn_id if load_turn is None else load_turn
        load_date = load_date
        control = self.filter(
            turn=turn_id,
            date_upload=load_date
        ).first()

        if control is None:
            control = self.create(
                created_by=user,
                turn=turn_id,
                date_upload=load_date,
            )

        return control
    

class PersonManager(BaseCheckingManager, ClockingBaseCheckingManager):

    def get_model(self):
        from src.peladoydescabezado.models import Person
        return Person

    def get_identity_fieldname(self):
        return "identity"
    

    def get_employers_with_production(self, date = None, category = 0):
        from src.peladoydescabezado.models import BasketProduction
        date = date if date is not None else datetime.now().date()
        queryset = (
            self
            .prefetch_related(
                Prefetch(
                    "product_baskets",
                    queryset=(
                        BasketProduction
                        .objects
                        .filter(control__date_upload=date)
                        .filter(table__category=category)
                        .select_related(
                            "control",
                            "table",

                        )
                    ),
                    to_attr="production"
                )       
            )
            .annotate(
                row=Window(
                    RowNumber(),
                    order_by=["lastnames", "names"]
                ),
                total=Sum(
                    "product_baskets__weight", filter=Q(product_baskets__control__date_upload=date, product_baskets__table__category=category)
                ),
                num_basckets=Count(
                    "product_baskets__weight", filter=Q(product_baskets__control__date_upload=date, product_baskets__table__category=category)
                ),
            )
        )


        return queryset
    

class BasketProductionManager(Manager):
    def weekly_record(self, start_date, end_date, category = 3):
        """
        Obtiene el peso total diario por persona y categoría en un rango de fechas.
        
        Args:
            start_date (date): Fecha de inicio
            end_date (date): Fecha de fin
            
        Returns:
            list: Lista de diccionarios con los resultados organizados por fecha
        """


        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        diccionario = {0: {}, 1: {}, 2: {}}
        fecha_actual = start_date
        daily_total = {}
        
        while fecha_actual <= end_date:
            date = fecha_actual.date() if isinstance(fecha_actual, datetime) else fecha_actual
            diccionario[0][date] = {}
            diccionario[1][date] = {}
            diccionario[2][date] = {}
            daily_total[date] = {"weight": Decimal(0), "baskets": Decimal(0)}
            fecha_actual += timedelta(days=1)
        
        resultados = self.filter(
            created__date__gte=start_date,
            created__date__lte=end_date,
            table__category=category
        ).values(
            'created__date',  # Agrupar por fecha (sin hora)
            'table__category',  # Agrupar por categoría de mesa
            'worker__id',       # Agrupar por trabajador (usamos ID para evitar duplicados)
            'worker__names',    # Incluir nombres del trabajador (opcional)
            'worker__lastnames', # Incluir apellidos del trabajador (opcional)
            'worker__identity',
            'turn',
        ).annotate(
            names=F("worker__names"),
            lastnames=F("worker__lastnames"),
            worker_id=F("worker__id"),
            identity=F("worker__identity"),
            total_sum=Sum('total'),  # Sumar el campo 'total'
            weight_sum=Sum('weight'), # Sumar el campo 'weight' (opcional)
            basket_count=Count("id"),
        ).order_by(
            'created__date', 'table__category', 'worker__id'
        )

        for resultado in resultados:
            diccionario[resultado["turn"]][resultado["created__date"]][f"{resultado['worker__identity']}"] = resultado
            daily_total[resultado["created__date"]]["weight"] += Decimal(resultado["weight_sum"])
            daily_total[resultado["created__date"]]["baskets"] += Decimal(resultado["basket_count"])

        return diccionario, resultados, daily_total