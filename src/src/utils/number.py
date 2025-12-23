import math

def truncate_float(valor_float, decimales):
    """
    Redondea un valor float al número de decimales especificado.
    
    Implementa el redondeo estándar (si el dígito siguiente es >= 5, redondea al alza).
    
    :param valor_float: El número flotante a redondear.
    :param decimales: El número de decimales a mantener.
    :return: El valor flotante redondeado.
    """
    if decimales < 0:
        raise ValueError("El número de decimales no puede ser negativo.")
        
    return round(valor_float, decimales)


def parse_float_to_time(decimal_hours):
    # 1. Obtener las horas (parte entera)
    hours = math.floor(decimal_hours)
    
    # 2. Obtener los minutos de la parte decimal restante
    minutes_decimal = (decimal_hours - hours) * 60
    minutes = math.floor(minutes_decimal)
    
    # 3. Obtener los segundos de la parte decimal de los minutos
    seconds = round((minutes_decimal - minutes) * 60)
    
    # Manejar el caso donde los segundos redondeen a 60
    if seconds == 60:
        seconds = 0
        minutes += 1
    if minutes == 60:
        minutes = 0
        hours += 1

    return f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"