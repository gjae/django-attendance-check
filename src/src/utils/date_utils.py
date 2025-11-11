from datetime import date, timedelta
from typing import Tuple, Union, List

def days_between_daterange(start_date: date, end_date: date) -> Tuple[date, ...]:
    """
    Calcula y retorna una tupla con todas las fechas que caen entre dos fechas dadas,
    incluyendo la fecha de inicio y la fecha de fin.

    :param start_date: La fecha de inicio del rango (datetime.date).
    :param end_date: La fecha de fin del rango (datetime.date).
    :return: Una tupla de objetos datetime.date.
    :raises ValueError: Si la fecha de inicio es posterior a la fecha de fin.
    """
    # 1. Validación de fechas
    if start_date > end_date:
        raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin.")

    # 2. Calcular la diferencia total de días (el rango)
    delta = end_date - start_date
    
    # 3. Generar la lista de fechas
    date_list: List[date] = []
    
    # Iterar desde el día 0 hasta el día total del rango
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        date_list.append(day)
    
    # 4. Retornar el resultado como una tupla
    return tuple(date_list)