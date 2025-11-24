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