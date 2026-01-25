# math_utils.py
"""
Utilidades matemáticas optimizadas para sistemas con pocos recursos.
Reemplaza funcionalidades de NumPy usando Python puro.
"""

import statistics


def calcular_media(valores):
    """Calcula la media (promedio) de una lista de valores"""
    if not valores:
        return 0
    return sum(valores) / len(valores)


def calcular_desviacion_estandar(valores):
    """Calcula la desviación estándar de una lista de valores"""
    if len(valores) < 2:
        return 0
    
    try:
        return statistics.stdev(valores)
    except (statistics.StatisticsError, ValueError):
        return 0


def calcular_varianza(valores):
    """Calcula la varianza de una lista de valores"""
    if len(valores) < 2:
        return 0
    
    try:
        return statistics.variance(valores)
    except (statistics.StatisticsError, ValueError):
        return 0


def obtener_rango(valores):
    """Obtiene min y max de una lista"""
    if not valores:
        return 0, 0
    return min(valores), max(valores)


def arange(start, stop=None, step=1):
    """
    Emula numpy.arange para crear secuencias.
    Mucho más ligero y eficiente.
    """
    if stop is None:
        stop = start
        start = 0
    
    result = []
    current = start
    if step > 0:
        while current < stop:
            result.append(current)
            current += step
    elif step < 0:
        while current > stop:
            result.append(current)
            current += step
    return result


def percentil(valores, percentil):
    """Calcula el percentil de una lista (ej: percentil 75)"""
    if not valores or percentil < 0 or percentil > 100:
        return 0
    
    valores_ordenados = sorted(valores)
    indice = (percentil / 100) * (len(valores_ordenados) - 1)
    
    # Interpolación lineal simple
    indice_bajo = int(indice)
    indice_alto = indice_bajo + 1
    
    if indice_alto >= len(valores_ordenados):
        return valores_ordenados[-1]
    
    fraccion = indice - indice_bajo
    return valores_ordenados[indice_bajo] * (1 - fraccion) + valores_ordenados[indice_alto] * fraccion
