from datetime import datetime
from model.data_manager import cargar_datos, obtener_estadisticas_concepto, cargar_historial_conceptos

def calcular_total_ingresos():
    """
    Calcula el total de todos los ingresos registrados.
    
    Returns:
        float: Suma total de los ingresos
    """
    try:
        ingresos = cargar_datos('ingresos')
        # Filtrar valores None o no numéricos y registros de historial
        return sum(ingreso[2] for ingreso in ingresos if ingreso[2] is not None and isinstance(ingreso[2], (int, float)) and ingreso[2] > 0)
    except Exception as e:
        print(f"Error al calcular total de ingresos: {e}")
        return 0.0

def obtener_ingresos_por_concepto(concepto):
    """
    Obtiene todos los ingresos de un concepto específico.
    
    Args:
        concepto (str): Concepto a buscar
        
    Returns:
        list: Lista de ingresos del concepto especificado
    """
    try:
        if not concepto or not isinstance(concepto, str):
            return []
            
        ingresos = cargar_datos('ingresos')
        return [ingreso for ingreso in ingresos if ingreso[1] == concepto and ingreso[2] is not None and ingreso[2] > 0]
    except Exception as e:
        print(f"Error al obtener ingresos por concepto: {e}")
        return []

def obtener_estadisticas_ingresos():
    """
    Obtiene estadísticas generales de los ingresos.
    
    Returns:
        dict: Diccionario con estadísticas
    """
    try:
        ingresos = cargar_datos('ingresos')
        # Filtrar montos válidos y registros que no son de historial
        montos = [ingreso[2] for ingreso in ingresos if ingreso[2] is not None and isinstance(ingreso[2], (int, float)) and ingreso[2] > 0]
        
        if not montos:
            return {
                'cantidad': 0,
                'total': 0,
                'promedio': 0,
                'minimo': 0,
                'maximo': 0
            }
        
        return {
            'cantidad': len(montos),
            'total': sum(montos),
            'promedio': sum(montos) / len(montos),
            'minimo': min(montos),
            'maximo': max(montos)
        }
    except Exception as e:
        print(f"Error al obtener estadísticas de ingresos: {e}")
        return {
            'cantidad': 0,
            'total': 0,
            'promedio': 0,
            'minimo': 0,
            'maximo': 0
        }

def obtener_ingresos_por_fecha(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene los ingresos dentro de un rango de fechas.
    
    Args:
        fecha_inicio (str, optional): Fecha de inicio en formato YYYY-MM-DD
        fecha_fin (str, optional): Fecha de fin en formato YYYY-MM-DD
        
    Returns:
        list: Lista de ingresos filtrados por fecha
    """
    try:
        ingresos = cargar_datos('ingresos')
        
        # Si no hay fechas especificadas, devolver todos los ingresos no históricos
        if fecha_inicio is None and fecha_fin is None:
            return [ingreso for ingreso in ingresos if ingreso[2] is not None and ingreso[2] > 0]
        
        ingresos_filtrados = []
        for ingreso in ingresos:
            # Solo considerar ingresos que tengan fecha (columna índice 3) y montos válidos
            if len(ingreso) > 3 and ingreso[3] and ingreso[2] is not None and ingreso[2] > 0:
                fecha_ingreso = ingreso[3]
                
                # Validar formato de fecha
                try:
                    if not isinstance(fecha_ingreso, str) or len(fecha_ingreso.split('-')) != 3:
                        continue
                    
                    # Filtrar por fecha de inicio
                    if fecha_inicio and fecha_ingreso < fecha_inicio:
                        continue
                        
                    # Filtrar por fecha de fin
                    if fecha_fin and fecha_ingreso > fecha_fin:
                        continue
                        
                    ingresos_filtrados.append(ingreso)
                except (ValueError, AttributeError):
                    # Saltear fechas con formato inválido
                    continue
        
        return ingresos_filtrados
    except Exception as e:
        print(f"Error al obtener ingresos por fecha: {e}")
        return []

def obtener_historial_detallado_conceptos():
    """
    Obtiene un historial detallado de todos los conceptos.
    
    Returns:
        dict: Diccionario con historial detallado por concepto
    """
    try:
        conceptos = cargar_historial_conceptos()
        historial = {}
        
        for concepto in conceptos:
            if not concepto or not isinstance(concepto, str):
                continue
                
            # Obtener estadísticas del concepto
            estadisticas = obtener_estadisticas_concepto(concepto)
            
            # Obtener todos los ingresos del concepto
            ingresos_concepto = obtener_ingresos_por_concepto(concepto)
            
            # Organizar los ingresos por fecha
            ingresos_detallados = []
            for ingreso in ingresos_concepto:
                fecha = ingreso[3] if len(ingreso) > 3 and ingreso[3] else "No especificada"
                monto = ingreso[2]
                
                if monto is not None and monto > 0:  # Filtrar registros válidos
                    ingresos_detallados.append({
                        'fecha': fecha,
                        'monto': monto
                    })
            
            # Ordenar por fecha (más reciente primero)
            ingresos_detallados.sort(
                key=lambda x: (
                    x['fecha'] if x['fecha'] != "No especificada" and isinstance(x['fecha'], str) else "0000-01-01"
                ), 
                reverse=True
            )
            
            # Guardar en el historial
            historial[concepto] = {
                'estadisticas': estadisticas,
                'ingresos': ingresos_detallados
            }
        
        return historial
    except Exception as e:
        print(f"Error al obtener historial detallado de conceptos: {e}")
        return {}