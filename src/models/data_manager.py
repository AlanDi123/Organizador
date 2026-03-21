# model/data_manager.py
"""
Gestor de datos mejorado con validación automática y type hints.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
import json
import shutil
import threading
import traceback
import functools
from functools import lru_cache
from pathlib import Path
from src.utils.db_migration import run_migrations
from src.utils.logger import get_logger
from src.utils.validators import Validator, ValidationError
from src.utils.decorators import timer, retry, safe_execute
from src.utils.paths import db_file, backup_file, db_dir
from src.config.env_config import DB_PATH

# Configurar logging
logger = get_logger('data_manager')

# Rutas de la base de datos (usando paths.py para Android compatibility)
DB_FILE = str(db_file())
BACKUP_FILE = str(backup_file())
DB_DIR = str(db_dir())

# Control de recursión para evitar bucles infinitos
EN_PROCESO_DE_RESTAURACION = False

# Singleton para gestionar las conexiones a la base de datos
class DBConnectionManager:
    """
    Administrador de conexiones a la base de datos.
    Implementa el patrón Thread-Local para SQLite.
    """
    _instance = None
    _local = threading.local()  # Almacenamiento local por hilo
    _db_file = DB_FILE
    
    @classmethod
    def get_instance(cls):
        """Obtiene la instancia única del manager (Singleton)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @timer
    @retry(max_attempts=3, delay=0.5)
    def get_connection(self) -> sqlite3.Connection:
        """
        Obtiene una conexión a la base de datos.
        Crea una nueva si no existe para el hilo actual.
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            try:
                # Crear una nueva conexión para este hilo
                self._local.connection = sqlite3.connect(self._db_file)
                # Configurar para devolver filas como diccionarios
                self._local.connection.row_factory = sqlite3.Row
                logger.debug(f"Nueva conexión creada para hilo {threading.get_ident()}")
            except Exception as e:
                logger.error(f"Error al crear conexión: {e}")
                raise
        
        return self._local.connection
    
    def close_connection(self):
        """Cierra la conexión para el hilo actual si existe"""
        if hasattr(self._local, 'connection') and self._local.connection is not None:
            try:
                self._local.connection.close()
                self._local.connection = None
                logger.debug(f"Conexión cerrada para hilo {threading.get_ident()}")
            except Exception as e:
                logger.error(f"Error al cerrar conexión: {e}")
                raise

# Función decoradora para medir el tiempo de ejecución
def measure_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Función {func.__name__} ejecutada en {end_time - start_time:.4f} segundos")
        return result
    return wrapper

def inicializar_db():
    """
    Inicializa la base de datos creando las tablas necesarias si no existen.
    También ejecuta migraciones si es necesario actualizar desde una versión anterior.
    
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """
    try:
        # Ejecutar migraciones primero
        if not run_migrations():
            logger.error("Error en la migración de la base de datos.")
            return False
        
        # Asegurar que el directorio exista
        os.makedirs(os.path.dirname(os.path.abspath(DB_FILE)), exist_ok=True)
        
        # Obtener conexión desde el manager
        conn = DBConnectionManager.get_instance().get_connection()
        cursor = conn.cursor()

        #Asegurar que el directorio exista
        os.makedirs(os.path.dirname(os.path.abspath(DB_FILE)), exist_ok=True)
        
        # Obtener conexión desde el manager
        conn = DBConnectionManager.get_instance().get_connection()
        cursor = conn.cursor()
        
        # Verificar si las tablas existen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gastos'")
        tabla_gastos_existe = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ingresos'")
        tabla_ingresos_existe = cursor.fetchone() is not None
        
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        if not tabla_gastos_existe:
            # Tabla de gastos con la columna es_historial
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    monto REAL NOT NULL CHECK(monto >= 0),
                    recurrente BOOLEAN DEFAULT 0,
                    fecha TEXT,
                    es_historial BOOLEAN DEFAULT 0,
                    fecha_creacion TEXT
                )
            ''')
            # Actualizar fecha_creacion con valor actual
            cursor.execute("UPDATE gastos SET fecha_creacion = datetime('now') WHERE fecha_creacion IS NULL")
        else:
            # Verificar si la columna es_historial existe
            try:
                cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
            except sqlite3.OperationalError:
                # La columna no existe, añadirla
                cursor.execute("ALTER TABLE gastos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
                
            # Verificar si la columna fecha_creacion existe
            try:
                cursor.execute("SELECT fecha_creacion FROM gastos LIMIT 1")
            except sqlite3.OperationalError:
                # Añadir columna sin valor predeterminado
                cursor.execute("ALTER TABLE gastos ADD COLUMN fecha_creacion TEXT")
                # Actualizar registros existentes con fecha actual
                cursor.execute("UPDATE gastos SET fecha_creacion = datetime('now') WHERE fecha_creacion IS NULL")
        
        if not tabla_ingresos_existe:
            # Tabla de ingresos con la columna es_historial
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ingresos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concepto TEXT NOT NULL,
                    monto REAL NOT NULL CHECK(monto >= 0),
                    fecha TEXT,
                    es_historial BOOLEAN DEFAULT 0,
                    fecha_creacion TEXT
                )
            ''')
            # Actualizar fecha_creacion con valor actual
            cursor.execute("UPDATE ingresos SET fecha_creacion = datetime('now') WHERE fecha_creacion IS NULL")
        else:
            # Verificar si la columna es_historial existe
            try:
                cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
            except sqlite3.OperationalError:
                # La columna no existe, añadirla
                cursor.execute("ALTER TABLE ingresos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
                
            # Verificar si la columna fecha_creacion existe
            try:
                cursor.execute("SELECT fecha_creacion FROM ingresos LIMIT 1")
            except sqlite3.OperationalError:
                # Añadir columna sin valor predeterminado
                cursor.execute("ALTER TABLE ingresos ADD COLUMN fecha_creacion TEXT")
                # Actualizar registros existentes con fecha actual
                cursor.execute("UPDATE ingresos SET fecha_creacion = datetime('now') WHERE fecha_creacion IS NULL")
        
        # Crear índices para mejorar rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_nombre ON gastos(nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_concepto ON ingresos(concepto)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_fecha ON ingresos(fecha)')
        
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_historial ON gastos(es_historial)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_historial ON ingresos(es_historial)')
        except sqlite3.OperationalError:
            # Los índices ya existen o hay otro problema
            pass
        
        # Confirmar transacción
        conn.commit()
        print("Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        print(traceback.format_exc())
        
        # Intentar hacer rollback si la conexión existe
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
        except:
            pass
            
        return False

#@measure_execution_time
@lru_cache(maxsize=32)

def importar_gastos(gastos_antiguos):
    """Importa gastos desde una base de datos antigua"""
    from datetime import datetime
    
    conn = DBConnectionManager.get_instance().get_connection()
    cursor = conn.cursor()
    importados = 0
    
    try:
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        for gasto in gastos_antiguos:
            try:
                # Extraer valores de manera segura según la estructura vista en el log
                # (id, nombre, monto, recurrente, fecha, es_historial, fecha_creacion)
                nombre = str(gasto[1]) if len(gasto) > 1 and gasto[1] is not None else "Gasto importado"
                
                monto = 0.0
                if len(gasto) > 2 and gasto[2] is not None:
                    try:
                        monto = float(gasto[2])
                    except (ValueError, TypeError):
                        monto = 0.0
                
                recurrente = 0
                if len(gasto) > 3 and gasto[3] is not None:
                    try:
                        recurrente = int(gasto[3])
                    except (ValueError, TypeError):
                        recurrente = 0
                
                fecha = datetime.now().strftime("%Y-%m-%d")
                if len(gasto) > 4 and gasto[4] is not None:
                    fecha = str(gasto[4])
                
                # Insertar sin verificar duplicados (evita el problema de hashable)
                cursor.execute("""
                    INSERT INTO gastos (nombre, monto, recurrente, fecha, fecha_creacion)
                    VALUES (?, ?, ?, ?, ?)
                """, (nombre, monto, recurrente, fecha, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                
                importados += 1
            except Exception as e:
                logger.error(f"Error al importar gasto individual: {e}")
                # Continuar con el siguiente en caso de error
                continue
        
        conn.commit()
        logger.info(f"Importados {importados} gastos")
        return importados
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al importar gastos: {e}")
        raise
        
def importar_ingresos(ingresos_antiguos):
    """Importa ingresos desde una base de datos antigua"""
    from datetime import datetime
    
    conn = DBConnectionManager.get_instance().get_connection()
    cursor = conn.cursor()
    importados = 0
    
    try:
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        for ingreso in ingresos_antiguos:
            try:
                # Extraer valores de manera segura según la estructura vista en el log
                # (id, concepto, monto, fecha, recurrente, fecha_creacion)
                concepto = str(ingreso[1]) if len(ingreso) > 1 and ingreso[1] is not None else "Ingreso importado"
                
                monto = 0.0
                if len(ingreso) > 2 and ingreso[2] is not None:
                    try:
                        monto = float(ingreso[2])
                    except (ValueError, TypeError):
                        monto = 0.0
                
                fecha = datetime.now().strftime("%Y-%m-%d")
                if len(ingreso) > 3 and ingreso[3] is not None:
                    fecha = str(ingreso[3])
                
                recurrente = 0
                if len(ingreso) > 4 and ingreso[4] is not None:
                    try:
                        recurrente = int(ingreso[4])
                    except (ValueError, TypeError):
                        recurrente = 0
                
                # Insertar sin verificar duplicados (evita el problema de hashable)
                cursor.execute("""
                    INSERT INTO ingresos (concepto, monto, fecha, recurrente, fecha_creacion)
                    VALUES (?, ?, ?, ?, ?)
                """, (concepto, monto, fecha, recurrente, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                
                importados += 1
            except Exception as e:
                logger.error(f"Error al importar ingreso individual: {e}")
                # Continuar con el siguiente en caso de error
                continue
        
        conn.commit()
        logger.info(f"Importados {importados} ingresos")
        return importados
    except Exception as e:
        conn.rollback()
        logger.error(f"Error al importar ingresos: {e}")
        raise
def cargar_datos(tabla, incluir_historial=False):
    """
    Carga todos los datos de una tabla específica.
    
    Args:
        tabla (str): Nombre de la tabla ('gastos' o 'ingresos')
        incluir_historial (bool): Si se incluyen los registros marcados como historial
        
    Returns:
        list: Lista de tuplas con los datos
    """
    try:
        # Validar el nombre de la tabla
        if tabla not in ('gastos', 'ingresos'):
            print(f"Tabla inválida: {tabla}")
            return []
            
        conn = DBConnectionManager.get_instance().get_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla tiene la columna es_historial
        tiene_columna_historial = True
        try:
            if tabla == 'gastos':
                cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
            elif tabla == 'ingresos':
                cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
        
        # Si no tiene la columna es_historial, cargar todos los datos
        if not tiene_columna_historial:
            if tabla == 'gastos':
                cursor.execute('SELECT * FROM gastos')
            elif tabla == 'ingresos':
                cursor.execute('SELECT * FROM ingresos')
        else:
            # Si tiene la columna, filtrar según el parámetro
            if tabla == 'gastos':
                if incluir_historial:
                    cursor.execute('SELECT * FROM gastos ORDER BY fecha DESC')
                else:
                    cursor.execute('SELECT * FROM gastos WHERE es_historial = 0 OR es_historial IS NULL ORDER BY fecha DESC')
            elif tabla == 'ingresos':
                if incluir_historial:
                    cursor.execute('SELECT * FROM ingresos ORDER BY fecha DESC')
                else:
                    cursor.execute('SELECT * FROM ingresos WHERE es_historial = 0 OR es_historial IS NULL ORDER BY fecha DESC')
        
        datos = cursor.fetchall()
        return datos
    except Exception as e:
        print(f"Error al cargar datos: {e}")
        print(traceback.format_exc())
        return []

def _actualizar_historial_gasto(nombre, recurrente):
    """
    Actualiza o crea una entrada en el historial de gastos.
    
    Args:
        nombre (str): Nombre del gasto
        recurrente (bool): Si el gasto es recurrente
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        if not nombre or nombre.strip() == "":
            return False
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # Verificar si la tabla tiene la columna es_historial
        tiene_columna_historial = True
        try:
            cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
            # Intentar añadir la columna
            try:
                cursor.execute("ALTER TABLE gastos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
                tiene_columna_historial = True
            except:
                conn.rollback()
                conn.close()
                return False
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
        if tiene_columna_historial:
            # Verificar si el nombre ya existe en el historial
            cursor.execute('SELECT id, recurrente FROM gastos WHERE nombre = ? AND es_historial = 1', (nombre,))
            resultado = cursor.fetchone()
            
            if resultado:
                # Si existe y el nuevo valor es recurrente, actualizar
                if recurrente != resultado[1]:
                    cursor.execute('UPDATE gastos SET recurrente = ? WHERE id = ?', 
                                (recurrente, resultado[0]))
            else:
                # Si no existe, crear nuevo registro de historial
                cursor.execute(
                    'INSERT INTO gastos (nombre, monto, recurrente, fecha, es_historial, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?)',
                    (nombre, 0, recurrente, fecha_actual, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
        else:
            # La tabla no tiene la columna es_historial, no podemos marcar registros como historial
            conn.rollback()
            conn.close()
            return False
        
        # Confirmar transacción
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al actualizar historial de gasto: {e}")
        print(traceback.format_exc())
        
        # Intentar hacer rollback si la conexión existe
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
        except:
            pass
            
        return False

def _actualizar_historial_concepto(concepto):
    """
    Actualiza o crea una entrada en el historial de conceptos.
    
    Args:
        concepto (str): Concepto de ingreso
        
    Returns:
        bool: True si se actualizó correctamente, False en caso contrario
    """
    try:
        if not concepto or concepto.strip() == "":
            return False
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # Verificar si la tabla tiene la columna es_historial
        tiene_columna_historial = True
        try:
            cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
            # Intentar añadir la columna
            try:
                cursor.execute("ALTER TABLE ingresos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
                tiene_columna_historial = True
            except:
                conn.rollback()
                conn.close()
                return False
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
        if tiene_columna_historial:
            # Verificar si el concepto ya existe en el historial
            cursor.execute('SELECT id FROM ingresos WHERE concepto = ? AND es_historial = 1', (concepto,))
            resultado = cursor.fetchone()
            
            if not resultado:
                # Si no existe, crear nuevo registro de historial
                cursor.execute(
                    'INSERT INTO ingresos (concepto, monto, fecha, es_historial, fecha_creacion) VALUES (?, ?, ?, ?, ?)',
                    (concepto, 0, fecha_actual, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
        else:
            # La tabla no tiene la columna es_historial
            conn.rollback()
            conn.close()
            return False
        
        # Confirmar transacción
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al actualizar historial de concepto: {e}")
        print(traceback.format_exc())
        
        # Intentar hacer rollback si la conexión existe
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
        except:
            pass
            
        return False

def guardar_gasto(nombre, monto, recurrente, fecha=None):
    """
    Guarda un nuevo gasto en la base de datos.
    
    Args:
        nombre (str): Nombre o descripción del gasto
        monto (float): Cantidad del gasto
        recurrente (bool): Si el gasto es recurrente o no
        fecha (str, optional): Fecha del gasto en formato YYYY-MM-DD
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Validar datos de entrada
        if not nombre or nombre.strip() == "":
            print("Error: Nombre de gasto vacío")
            return False
            
        try:
            monto = float(monto)
            if monto <= 0:
                print("Error: Monto debe ser mayor que cero")
                return False
        except (ValueError, TypeError):
            print(f"Error: Monto inválido - {monto}")
            return False
            
        recurrente = bool(recurrente)
        
        # Validar formato de fecha
        if fecha:
            try:
                datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                print(f"Error: Formato de fecha inválido - {fecha}")
                return False
        else:
            fecha = datetime.now().strftime("%Y-%m-%d")
        
        conn = DBConnectionManager.get_instance().get_connection()
        cursor = conn.cursor()
        
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # Verificar si la tabla tiene la columna es_historial y fecha_creacion
        tiene_columna_historial = True
        tiene_columna_fecha = True
        
        try:
            cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
        
        try:
            cursor.execute("SELECT fecha_creacion FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_fecha = False
        
        # Preparar el timestamp actual
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insertar el gasto
        if tiene_columna_historial and tiene_columna_fecha:
            cursor.execute(
                'INSERT INTO gastos (nombre, monto, recurrente, fecha, es_historial, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?)',
                (nombre, monto, recurrente, fecha, 0, now)  # No es historial
            )
        elif tiene_columna_historial:
            cursor.execute(
                'INSERT INTO gastos (nombre, monto, recurrente, fecha, es_historial) VALUES (?, ?, ?, ?, ?)',
                (nombre, monto, recurrente, fecha, 0)  # No es historial
            )
        elif tiene_columna_fecha:
            cursor.execute(
                'INSERT INTO gastos (nombre, monto, recurrente, fecha, fecha_creacion) VALUES (?, ?, ?, ?, ?)',
                (nombre, monto, recurrente, fecha, now)
            )
        else:
            cursor.execute(
                'INSERT INTO gastos (nombre, monto, recurrente, fecha) VALUES (?, ?, ?, ?)',
                (nombre, monto, recurrente, fecha)
            )
        
        conn.commit()
        
        # Actualizar el historial
        _actualizar_historial_gasto(nombre, recurrente)
        
        # Invalidar caché
        if hasattr(cargar_datos, 'cache_clear'):
            cargar_datos.cache_clear()
        
        return True
    except Exception as e:
        print(f"Error al guardar gasto: {e}")
        print(traceback.format_exc())
        
        # Intentar hacer rollback si la conexión existe
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
        except:
            pass
            
        return False

def guardar_ingreso(concepto, monto, fecha=None):
    """
    Guarda un nuevo ingreso en la base de datos.
    
    Args:
        concepto (str): Concepto o descripción del ingreso
        monto (float): Cantidad del ingreso
        fecha (str, optional): Fecha del ingreso en formato YYYY-MM-DD
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Validar datos de entrada
        if not concepto or concepto.strip() == "":
            print("Error: Concepto de ingreso vacío")
            return False
            
        try:
            monto = float(monto)
            if monto <= 0:
                print("Error: Monto debe ser mayor que cero")
                return False
        except (ValueError, TypeError):
            print(f"Error: Monto inválido - {monto}")
            return False
        
        # Validar formato de fecha
        if fecha:
            try:
                datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                print(f"Error: Formato de fecha inválido - {fecha}")
                return False
        else:
            fecha = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # Verificar si la tabla tiene la columna es_historial y fecha_creacion
        tiene_columna_historial = True
        tiene_columna_fecha = True
        
        try:
            cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
        
        try:
            cursor.execute("SELECT fecha_creacion FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_fecha = False
        
        # Preparar el timestamp actual
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insertar el ingreso
        if tiene_columna_historial and tiene_columna_fecha:
            cursor.execute(
                'INSERT INTO ingresos (concepto, monto, fecha, es_historial, fecha_creacion) VALUES (?, ?, ?, ?, ?)',
                (concepto, monto, fecha, 0, now)  # No es historial
            )
        elif tiene_columna_historial:
            cursor.execute(
                'INSERT INTO ingresos (concepto, monto, fecha, es_historial) VALUES (?, ?, ?, ?)',
                (concepto, monto, fecha, 0)  # No es historial
            )
        elif tiene_columna_fecha:
            cursor.execute(
                'INSERT INTO ingresos (concepto, monto, fecha, fecha_creacion) VALUES (?, ?, ?, ?)',
                (concepto, monto, fecha, now)
            )
        else:
            cursor.execute(
                'INSERT INTO ingresos (concepto, monto, fecha) VALUES (?, ?, ?)',
                (concepto, monto, fecha)
            )
        
        conn.commit()
        conn.close()
        
        # Actualizar el historial
        _actualizar_historial_concepto(concepto)
        
        return True
    except Exception as e:
        print(f"Error al guardar ingreso: {e}")
        print(traceback.format_exc())
        
        # Intentar hacer rollback si la conexión existe
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
        except:
            pass
            
        return False

def eliminar_dato(tabla, campo, valor):
    """
    Elimina un dato específico de una tabla.
    
    Args:
        tabla (str): Nombre de la tabla ('gastos' o 'ingresos')
        campo (str): Campo por el que se buscará (nombre, concepto)
        valor (str): Valor del campo a buscar
        
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        # Validar parámetros
        if tabla not in ('gastos', 'ingresos'):
            print(f"Tabla inválida: {tabla}")
            return False
            
        if not campo or not valor:
            print("Campo o valor inválido")
            return False
            
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # Sanitizar el campo para evitar SQL injection
        campos_validos = {
            'gastos': ['id', 'nombre'],
            'ingresos': ['id', 'concepto']
        }
        
        if campo not in campos_validos[tabla]:
            print(f"Campo inválido: {campo}")
            conn.rollback()
            conn.close()
            return False
        
        # Verificar si la tabla tiene la columna es_historial
        tiene_columna_historial = True
        try:
            if tabla == 'gastos':
                cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
            elif tabla == 'ingresos':
                cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
        
        # Eliminar datos, evitando borrar registros históricos si es posible
        if tiene_columna_historial:
            if tabla == 'gastos':
                cursor.execute(f'DELETE FROM gastos WHERE {campo} = ? AND (es_historial = 0 OR es_historial IS NULL)', (valor,))
            elif tabla == 'ingresos':
                cursor.execute(f'DELETE FROM ingresos WHERE {campo} = ? AND (es_historial = 0 OR es_historial IS NULL)', (valor,))
        else:
            if tabla == 'gastos':
                cursor.execute(f'DELETE FROM gastos WHERE {campo} = ?', (valor,))
            elif tabla == 'ingresos':
                cursor.execute(f'DELETE FROM ingresos WHERE {campo} = ?', (valor,))
        
        rowcount = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rowcount > 0
    except Exception as e:
        print(f"Error al eliminar dato: {e}")
        print(traceback.format_exc())
        
        # Intentar hacer rollback si la conexión existe
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
        except:
            pass
            
        return False

def crear_backup_antes_borrar():
    """
    Crea una copia de seguridad de la base de datos antes de borrar todos los datos.
    
    Returns:
        str: Ruta del archivo de backup, o None si falló
    """
    try:
        # Verificar que la base de datos existe
        if not os.path.exists(DB_FILE):
            print(f"No se encontró la base de datos para hacer backup: {DB_FILE}")
            return None
            
        # Crear directorio de backups si no existe
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
            
        # Crear nombre para el backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f'finanzas_backup_{timestamp}.db')
        
        # Hacer la copia
        shutil.copy2(DB_FILE, backup_path)
        print(f"Backup creado en: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Error al crear backup: {e}")
        print(traceback.format_exc())
        return None

def eliminar_todos_datos():
    """
    Elimina todos los datos de las tablas excepto los registros de historial.
    Realiza un backup automático antes de borrar.
    
    Returns:
        bool: True si se eliminaron correctamente, False en caso contrario
    """
    try:
        # Crear backup antes de borrar
        backup_path = crear_backup_antes_borrar()
        if not backup_path:
            print("Advertencia: No se pudo crear backup antes de borrar")
        
        # Asegurar que el historial está actualizado con los nombres/conceptos actuales
        sincronizar_historiales()
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # Verificar si las tablas tienen la columna es_historial
        tiene_columna_gastos_historial = True
        tiene_columna_ingresos_historial = True
        
        try:
            cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_gastos_historial = False
            
        try:
            cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_ingresos_historial = False
        
        # Eliminar datos, evitando borrar registros históricos si es posible
        if tiene_columna_gastos_historial:
            cursor.execute('DELETE FROM gastos WHERE es_historial = 0 OR es_historial IS NULL')
        else:
            # Si no tiene la columna, agregar la columna y marcar todos los registros como no históricos
            try:
                cursor.execute("ALTER TABLE gastos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
                tiene_columna_gastos_historial = True
                
                # Crear registros históricos
                cursor.execute("""
                    INSERT INTO gastos (nombre, monto, recurrente, fecha, es_historial)
                    SELECT DISTINCT nombre, 0, MAX(recurrente), datetime('now'), 1
                    FROM gastos
                    GROUP BY nombre
                """)
                
                # Eliminar los registros no históricos
                cursor.execute('DELETE FROM gastos WHERE es_historial = 0 OR es_historial IS NULL')
            except Exception as e:
                print(f"Error al añadir columna es_historial a gastos: {e}")
                # Si no se puede agregar la columna, no borrar nada para no perder el historial
                conn.rollback()
                conn.close()
                return False
            
        if tiene_columna_ingresos_historial:
            cursor.execute('DELETE FROM ingresos WHERE es_historial = 0 OR es_historial IS NULL')
        else:
            # Si no tiene la columna, agregar la columna y marcar todos los registros como no históricos
            try:
                cursor.execute("ALTER TABLE ingresos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
                tiene_columna_ingresos_historial = True
                
                # Crear registros históricos
                cursor.execute("""
                    INSERT INTO ingresos (concepto, monto, fecha, es_historial)
                    SELECT DISTINCT concepto, 0, datetime('now'), 1
                    FROM ingresos
                    GROUP BY concepto
                """)
                
                # Eliminar los registros no históricos
                cursor.execute('DELETE FROM ingresos WHERE es_historial = 0 OR es_historial IS NULL')
            except Exception as e:
                print(f"Error al añadir columna es_historial a ingresos: {e}")
                # Si no se puede agregar la columna, no borrar nada para no perder el historial
                conn.rollback()
                conn.close()
                return False
        
        conn.commit()
        conn.close()
        
        print("Datos eliminados correctamente (historial preservado)")
        return True
    except Exception as e:
        print(f"Error al eliminar todos los datos: {e}")
        print(traceback.format_exc())
        
        # Intentar hacer rollback si la conexión existe
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
        except:
            pass
            
        return False

def cargar_historial_conceptos():
    """
    Obtiene una lista de conceptos únicos del historial.
    
    Returns:
        list: Lista de conceptos únicos
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si la tabla tiene la columna es_historial
        tiene_columna_historial = True
        try:
            cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
        
        # Buscar conceptos según si tiene la columna es_historial o no
        if tiene_columna_historial:
            # Buscar conceptos en registros de historial
            cursor.execute('SELECT DISTINCT concepto FROM ingresos WHERE es_historial = 1 ORDER BY concepto')
        else:
            # Si no tiene la columna, obtener todos los conceptos únicos
            cursor.execute('SELECT DISTINCT concepto FROM ingresos ORDER BY concepto')
        
        # Extraer solo los conceptos
        conceptos = [concepto[0] for concepto in cursor.fetchall() if concepto[0]]
        
        conn.close()
        return conceptos
    except Exception as e:
        print(f"Error al cargar historial de conceptos: {e}")
        print(traceback.format_exc())
        return []

def cargar_historial_gastos():
    """
    Obtiene una lista de nombres únicos de gastos del historial.
    
    Returns:
        list: Lista de nombres de gastos únicos
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si la tabla tiene la columna es_historial
        tiene_columna_historial = True
        try:
            cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
        
        # Buscar nombres según si tiene la columna es_historial o no
        if tiene_columna_historial:
            # Buscar nombres en registros de historial
            cursor.execute('SELECT DISTINCT nombre FROM gastos WHERE es_historial = 1 ORDER BY nombre')
        else:
            # Si no tiene la columna, obtener todos los nombres únicos
            cursor.execute('SELECT DISTINCT nombre FROM gastos ORDER BY nombre')
        
        # Extraer solo los nombres
        nombres = [nombre[0] for nombre in cursor.fetchall() if nombre[0]]
        
        conn.close()
        return nombres
    except Exception as e:
        print(f"Error al cargar historial de gastos: {e}")
        print(traceback.format_exc())
        return []

def obtener_info_gasto_historial(nombre):
    """
    Obtiene información básica de un gasto desde el historial.
    
    Args:
        nombre (str): Nombre del gasto a buscar
        
    Returns:
        dict: Diccionario con información del gasto (recurrente)
    """
    try:
        if not nombre or not isinstance(nombre, str):
            return {'nombre': nombre, 'recurrente': False}
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si la tabla tiene la columna es_historial
        tiene_columna_historial = True
        try:
            cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
        
        if tiene_columna_historial:
            cursor.execute('SELECT recurrente FROM gastos WHERE nombre = ? AND es_historial = 1', (nombre,))
        else:
            # Si no tiene la columna, obtener cualquier gasto con ese nombre
            cursor.execute('SELECT recurrente FROM gastos WHERE nombre = ? LIMIT 1', (nombre,))
            
        resultado = cursor.fetchone()
        es_recurrente = bool(resultado[0]) if resultado else False
        
        conn.close()
        
        return {
            'nombre': nombre,
            'recurrente': es_recurrente
        }
    except Exception as e:
        print(f"Error al obtener información del gasto desde historial: {e}")
        print(traceback.format_exc())
        return {
            'nombre': nombre,
            'recurrente': False
        }

def obtener_estadisticas_concepto(concepto):
    """
    Obtiene estadísticas para un concepto específico.
    
    Args:
        concepto (str): Concepto a buscar
        
    Returns:
        dict: Diccionario con estadísticas
    """
    try:
        if not concepto or not isinstance(concepto, str):
            return {
                'cantidad': 0,
                'total': 0,
                'promedio': 0,
                'minimo': 0,
                'maximo': 0
            }
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si la tabla tiene la columna es_historial
        tiene_columna_historial = True
        try:
            cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
        
        # Consulta SQL según si tiene la columna es_historial o no
        if tiene_columna_historial:
            cursor.execute('''
                SELECT 
                    COUNT(*) as cantidad,
                    SUM(monto) as total,
                    AVG(monto) as promedio,
                    MIN(monto) as minimo,
                    MAX(monto) as maximo
                FROM ingresos
                WHERE concepto = ? AND monto > 0 AND (es_historial = 0 OR es_historial IS NULL)
            ''', (concepto,))
        else:
            cursor.execute('''
                SELECT 
                    COUNT(*) as cantidad,
                    SUM(monto) as total,
                    AVG(monto) as promedio,
                    MIN(monto) as minimo,
                    MAX(monto) as maximo
                FROM ingresos
                WHERE concepto = ? AND monto > 0
            ''', (concepto,))
        
        resultado = cursor.fetchone()
        
        if resultado and resultado[0] > 0:
            estadisticas = {
                'cantidad': resultado[0],
                'total': resultado[1],
                'promedio': resultado[2],
                'minimo': resultado[3],
                'maximo': resultado[4]
            }
        else:
            estadisticas = {
                'cantidad': 0,
                'total': 0,
                'promedio': 0,
                'minimo': 0,
                'maximo': 0
            }
        
        conn.close()
        return estadisticas
    except Exception as e:
        print(f"Error al obtener estadísticas del concepto: {e}")
        print(traceback.format_exc())
        return {
            'cantidad': 0,
            'total': 0,
            'promedio': 0,
            'minimo': 0,
            'maximo': 0
        }

def obtener_estadisticas_gasto(nombre):
    """
    Obtiene estadísticas para un gasto específico.
    
    Args:
        nombre (str): Nombre del gasto a buscar
        
    Returns:
        dict: Diccionario con estadísticas
    """
    try:
        if not nombre or not isinstance(nombre, str):
            return {
                'cantidad': 0,
                'total': 0,
                'promedio': 0,
                'minimo': 0,
                'maximo': 0,
                'recurrente': False
            }
            
        # Primero, obtener el estado recurrente del historial
        info_historial = obtener_info_gasto_historial(nombre)
        es_recurrente = info_historial.get('recurrente', False)
        
        # Luego, obtener estadísticas, excluyendo registros de historial si es posible
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si la tabla tiene la columna es_historial
        tiene_columna_historial = True
        try:
            cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_historial = False
        
        # Consulta SQL según si tiene la columna es_historial o no
        if tiene_columna_historial:
            cursor.execute('''
                SELECT 
                    COUNT(*) as cantidad,
                    SUM(monto) as total,
                    AVG(monto) as promedio,
                    MIN(monto) as minimo,
                    MAX(monto) as maximo
                FROM gastos
                WHERE nombre = ? AND monto > 0 AND (es_historial = 0 OR es_historial IS NULL)
            ''', (nombre,))
        else:
            cursor.execute('''
                SELECT 
                    COUNT(*) as cantidad,
                    SUM(monto) as total,
                    AVG(monto) as promedio,
                    MIN(monto) as minimo,
                    MAX(monto) as maximo
                FROM gastos
                WHERE nombre = ? AND monto > 0
            ''', (nombre,))
        
        resultado = cursor.fetchone()
        
        if resultado and resultado[0] > 0:
            estadisticas = {
                'cantidad': resultado[0],
                'total': resultado[1],
                'promedio': resultado[2],
                'minimo': resultado[3],
                'maximo': resultado[4],
                'recurrente': es_recurrente
            }
        else:
            estadisticas = {
                'cantidad': 0,
                'total': 0,
                'promedio': 0,
                'minimo': 0,
                'maximo': 0,
                'recurrente': es_recurrente
            }
        
        conn.close()
        return estadisticas
    except Exception as e:
        print(f"Error al obtener estadísticas del gasto: {e}")
        print(traceback.format_exc())
        return {
            'cantidad': 0,
            'total': 0,
            'promedio': 0,
            'minimo': 0,
            'maximo': 0,
            'recurrente': False
        }

def sincronizar_historiales():
    """
    Sincroniza los datos actuales con el historial para asegurar que todos los
    conceptos y gastos estén en el historial.
    
    Returns:
        bool: True si la sincronización fue exitosa, False en caso contrario
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()
        
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # Verificar si las tablas tienen la columna es_historial
        tiene_columna_gastos_historial = True
        tiene_columna_ingresos_historial = True
        
        try:
            cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_gastos_historial = False
            # Intentar añadir la columna
            try:
                cursor.execute("ALTER TABLE gastos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
                tiene_columna_gastos_historial = True
            except Exception as e:
                print(f"Error al añadir columna es_historial a gastos: {e}")
                conn.rollback()
                conn.close()
                return False
            
        try:
            cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_ingresos_historial = False
            # Intentar añadir la columna
            try:
                cursor.execute("ALTER TABLE ingresos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
                tiene_columna_ingresos_historial = True
            except Exception as e:
                print(f"Error al añadir columna es_historial a ingresos: {e}")
                conn.rollback()
                conn.close()
                return False
        
        # No podemos sincronizar el historial si no hay columna es_historial
        if not tiene_columna_gastos_historial or not tiene_columna_ingresos_historial:
            conn.rollback()
            conn.close()
            return False
        
        # Verificar columna fecha_creacion en gastos
        tiene_columna_fecha_gastos = True
        try:
            cursor.execute("SELECT fecha_creacion FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_fecha_gastos = False
            # No intentamos añadir la columna aquí, ya que podría fallar
        
        # Verificar columna fecha_creacion en ingresos
        tiene_columna_fecha_ingresos = True
        try:
            cursor.execute("SELECT fecha_creacion FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            tiene_columna_fecha_ingresos = False
            # No intentamos añadir la columna aquí, ya que podría fallar
        
        # Sincronizar gastos
        cursor.execute('SELECT DISTINCT nombre, MAX(recurrente) FROM gastos GROUP BY nombre')
        gastos = cursor.fetchall()
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
        for nombre, recurrente in gastos:
            if nombre and nombre.strip():
                # Verificar si ya existe un registro histórico
                cursor.execute('SELECT id FROM gastos WHERE nombre = ? AND es_historial = 1', (nombre,))
                if not cursor.fetchone():
                    # Preparar la inserción según las columnas que existan
                    if tiene_columna_fecha_gastos:
                        cursor.execute(
                            'INSERT INTO gastos (nombre, monto, recurrente, fecha, es_historial, fecha_creacion) VALUES (?, ?, ?, ?, ?, ?)',
                            (nombre, 0, recurrente, fecha_actual, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        )
                    else:
                        cursor.execute(
                            'INSERT INTO gastos (nombre, monto, recurrente, fecha, es_historial) VALUES (?, ?, ?, ?, ?)',
                            (nombre, 0, recurrente, fecha_actual, 1)
                        )
        
        # Sincronizar conceptos de ingresos
        cursor.execute('SELECT DISTINCT concepto FROM ingresos')
        conceptos = cursor.fetchall()
        
        for (concepto,) in conceptos:
            if concepto and concepto.strip():
                # Verificar si ya existe un registro histórico
                cursor.execute('SELECT id FROM ingresos WHERE concepto = ? AND es_historial = 1', (concepto,))
                if not cursor.fetchone():
                    # Preparar la inserción según las columnas que existan
                    if tiene_columna_fecha_ingresos:
                        cursor.execute(
                            'INSERT INTO ingresos (concepto, monto, fecha, es_historial, fecha_creacion) VALUES (?, ?, ?, ?, ?)',
                            (concepto, 0, fecha_actual, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        )
                    else:
                        cursor.execute(
                            'INSERT INTO ingresos (concepto, monto, fecha, es_historial) VALUES (?, ?, ?, ?)',
                            (concepto, 0, fecha_actual, 1)
                        )
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error al sincronizar historiales: {e}")
        print(traceback.format_exc())
        
        # Intentar hacer rollback si la conexión existe
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
        except:
            pass
            
        return False

def restaurar_base_datos(ruta_backup=None):
    """
    Restaura la base de datos desde un archivo de backup.
    
    Args:
        ruta_backup (str, optional): Ruta al archivo de backup. Si es None,
                                    se usará el backup más reciente.
                                    
    Returns:
        bool: True si la restauración fue exitosa, False en caso contrario
    """
    global EN_PROCESO_DE_RESTAURACION
    
    if EN_PROCESO_DE_RESTAURACION:
        print("Ya hay una restauración en proceso. Espere a que termine.")
        return False
        
    try:
        EN_PROCESO_DE_RESTAURACION = True
        
        # Si no se especifica ruta, buscar el backup más reciente
        if not ruta_backup:
            backup_dir = 'backups'
            if not os.path.exists(backup_dir):
                print(f"No se encontró directorio de backups: {backup_dir}")
                EN_PROCESO_DE_RESTAURACION = False
                return False
                
            backups = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
                      if f.startswith('finanzas_backup_') and f.endswith('.db')]
                      
            if not backups:
                print("No se encontraron archivos de backup")
                EN_PROCESO_DE_RESTAURACION = False
                return False
                
            # Ordenar por fecha (más reciente primero)
            backups.sort(key=os.path.getmtime, reverse=True)
            ruta_backup = backups[0]
        
        # Verificar que el backup existe
        if not os.path.exists(ruta_backup):
            print(f"No se encontró el archivo de backup: {ruta_backup}")
            EN_PROCESO_DE_RESTAURACION = False
            return False
            
        # Hacer backup del archivo actual antes de restaurar
        if os.path.exists(DB_FILE):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_antes_restauracion = f'finanzas_pre_restauracion_{timestamp}.db'
            
            backup_dir = 'backups'
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
                
            backup_path = os.path.join(backup_dir, backup_antes_restauracion)
            
            shutil.copy2(DB_FILE, backup_path)
            print(f"Base de datos actual respaldada en: {backup_path}")
        
        # Copiar el backup a la ubicación de la base de datos
        shutil.copy2(ruta_backup, DB_FILE)
        print(f"Base de datos restaurada desde: {ruta_backup}")
        
        # Verificar que la restauración fue exitosa
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas = cursor.fetchall()
            
            if not tablas:
                print("Error: La base de datos restaurada no contiene tablas")
                conn.close()
                EN_PROCESO_DE_RESTAURACION = False
                return False
                
            print(f"Restauración exitosa. Tablas encontradas: {[t[0] for t in tablas]}")
            conn.close()
            
            # Sincronizar historiales para asegurar la integridad
            sincronizar_historiales()
            
            EN_PROCESO_DE_RESTAURACION = False
            return True
        except Exception as e:
            print(f"Error al verificar la base de datos restaurada: {e}")
            conn.close()
            EN_PROCESO_DE_RESTAURACION = False
            return False
            
    except Exception as e:
        print(f"Error al restaurar la base de datos: {e}")
        print(traceback.format_exc())
        EN_PROCESO_DE_RESTAURACION = False
        return False

# Inicializar base de datos al importar el módulo (opcional)
# inicializar_db()