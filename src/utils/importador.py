# model/importador.py
import sqlite3
import os
import logging
from datetime import datetime

# Configuración de logging
logger = logging.getLogger('importador')

def importar_datos_directamente(datos_gastos, datos_ingresos, db_path=None):
    """
    Importa datos directamente a la base de datos sin usar las funciones existentes
    """
    from src.models.data_manager import DBConnectionManager
    
    # Obtener conexión para este hilo
    conn = DBConnectionManager.get_instance().get_connection()
    cursor = conn.cursor()
    
    gastos_importados = 0
    ingresos_importados = 0
    
    try:
        # Comenzar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # Importar gastos
        if datos_gastos:
            for gasto in datos_gastos:
                try:
                    # Extraer campos relevantes
                    nombre = str(gasto[1]) if len(gasto) > 1 else "Gasto importado"
                    
                    # Convertir monto a float
                    monto = 0.0
                    if len(gasto) > 2:
                        try:
                            monto = float(gasto[2]) if gasto[2] is not None else 0.0
                        except:
                            monto = 0.0
                    
                    # Otros campos
                    recurrente = 0
                    if len(gasto) > 3:
                        try:
                            recurrente = int(gasto[3]) if gasto[3] is not None else 0
                        except:
                            recurrente = 0
                    
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    if len(gasto) > 4 and gasto[4]:
                        fecha = str(gasto[4])
                    
                    # Insertar en la base de datos
                    cursor.execute("""
                        INSERT INTO gastos (nombre, monto, recurrente, fecha, fecha_creacion)
                        VALUES (?, ?, ?, ?, ?)
                    """, (nombre, monto, recurrente, fecha, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    
                    gastos_importados += 1
                    
                except Exception as e:
                    logger.error(f"Error importando gasto: {e}")
                    # Continuar con el siguiente gasto
                    continue
        
        # Importar ingresos
        if datos_ingresos:
            for ingreso in datos_ingresos:
                try:
                    # Extraer campos relevantes
                    concepto = str(ingreso[1]) if len(ingreso) > 1 else "Ingreso importado"
                    
                    # Convertir monto a float
                    monto = 0.0
                    if len(ingreso) > 2:
                        try:
                            monto = float(ingreso[2]) if ingreso[2] is not None else 0.0
                        except:
                            monto = 0.0
                    
                    # Otros campos
                    fecha = datetime.now().strftime("%Y-%m-%d")
                    if len(ingreso) > 3 and ingreso[3]:
                        fecha = str(ingreso[3])
                    
                    recurrente = 0
                    if len(ingreso) > 4:
                        try:
                            recurrente = int(ingreso[4]) if ingreso[4] is not None else 0
                        except:
                            recurrente = 0
                    
                    # Insertar en la base de datos
                    cursor.execute("""
                        INSERT INTO ingresos (concepto, monto, fecha, recurrente, fecha_creacion)
                        VALUES (?, ?, ?, ?, ?)
                    """, (concepto, monto, fecha, recurrente, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    
                    ingresos_importados += 1
                    
                except Exception as e:
                    logger.error(f"Error importando ingreso: {e}")
                    # Continuar con el siguiente ingreso
                    continue
        
        # Confirmar cambios
        conn.commit()
        logger.info(f"Importación directa completada: {gastos_importados} gastos, {ingresos_importados} ingresos")
        
        # Devolver un diccionario en lugar de una tupla (para evitar error 'tuple' has no attribute 'get')
        return {"gastos": gastos_importados, "ingresos": ingresos_importados}
        
    except Exception as e:
        # Rollback en caso de error
        conn.rollback()
        logger.error(f"Error durante la importación directa: {e}")
        raise