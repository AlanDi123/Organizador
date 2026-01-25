from datetime import datetime
from src.models.data_manager import cargar_datos

def calcular_total_gastos():
    """
    Calcula el total de todos los gastos registrados.
    
    Returns:
        float: Suma total de los gastos
    """
    try:
        gastos = cargar_datos('gastos')
        # Filtrar valores None o no numéricos y registros de historial
        return sum(gasto[2] for gasto in gastos if gasto[2] is not None and isinstance(gasto[2], (int, float)) and gasto[2] > 0)
    except Exception as e:
        print(f"Error al calcular total de gastos: {e}")
        return 0.0

def calcular_gastos_recurrentes():
    """
    Calcula el total de los gastos recurrentes.
    
    Returns:
        float: Suma total de los gastos recurrentes
    """
    try:
        gastos = cargar_datos('gastos')
        # Filtrar registros de historial y asegurarse que recurrente es True
        return sum(gasto[2] for gasto in gastos if len(gasto) > 3 and gasto[3] and gasto[2] is not None and gasto[2] > 0)
    except Exception as e:
        print(f"Error al calcular gastos recurrentes: {e}")
        return 0.0

def calcular_gastos_no_recurrentes():
    """
    Calcula el total de los gastos no recurrentes.
    
    Returns:
        float: Suma total de los gastos no recurrentes
    """
    try:
        gastos = cargar_datos('gastos')
        # Filtrar registros de historial y asegurarse que recurrente es False
        return sum(gasto[2] for gasto in gastos if len(gasto) > 3 and not gasto[3] and gasto[2] is not None and gasto[2] > 0)
    except Exception as e:
        print(f"Error al calcular gastos no recurrentes: {e}")
        return 0.0

def obtener_gastos_por_fecha(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene los gastos dentro de un rango de fechas.
    
    Args:
        fecha_inicio (str, optional): Fecha de inicio en formato YYYY-MM-DD
        fecha_fin (str, optional): Fecha de fin en formato YYYY-MM-DD
        
    Returns:
        list: Lista de gastos filtrados por fecha
    """
    try:
        gastos = cargar_datos('gastos')
        
        # Si no hay fechas especificadas, devolver todos los gastos (no históricos)
        if fecha_inicio is None and fecha_fin is None:
            return [gasto for gasto in gastos if gasto[2] is not None and gasto[2] > 0]
        
        gastos_filtrados = []
        for gasto in gastos:
            # Solo considerar gastos que tengan fecha (columna índice 4) y montos válidos
            if len(gasto) > 4 and gasto[4] and gasto[2] is not None and gasto[2] > 0:
                fecha_gasto = gasto[4]
                
                # Validar formato de fecha
                try:
                    if not isinstance(fecha_gasto, str) or len(fecha_gasto.split('-')) != 3:
                        continue
                    
                    # Filtrar por fecha de inicio
                    if fecha_inicio and fecha_gasto < fecha_inicio:
                        continue
                        
                    # Filtrar por fecha de fin
                    if fecha_fin and fecha_gasto > fecha_fin:
                        continue
                        
                    gastos_filtrados.append(gasto)
                except (ValueError, AttributeError):
                    # Saltear fechas con formato inválido
                    continue
        
        return gastos_filtrados
    except Exception as e:
        print(f"Error al obtener gastos por fecha: {e}")
        return []

def obtener_gastos_por_nombre(nombre):
    """
    Obtiene todos los gastos con un nombre específico.
    
    Args:
        nombre (str): Nombre del gasto a buscar
        
    Returns:
        list: Lista de gastos con el nombre especificado
    """
    try:
        gastos = cargar_datos('gastos')
        return [gasto for gasto in gastos if gasto[1] == nombre and gasto[2] is not None and gasto[2] > 0]
    except Exception as e:
        print(f"Error al obtener gastos por nombre: {e}")
        return []