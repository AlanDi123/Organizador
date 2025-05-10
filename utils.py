import os
import sys
import threading
import traceback
import logging
from functools import wraps
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='organizador_finanzas.log'
)
logger = logging.getLogger('utils')

# Decorador para medir tiempo de ejecución
def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"Función {func.__name__} tomó {end_time - start_time:.4f} segundos")
        return result
    return wrapper

# Importación condicional para el manejador de bases de datos
try:
    from model.data_manager import inicializar_db, DBConnectionManager
except ImportError:
    # La importación por defecto para la inicialización básica
    from model.data_manager import inicializar_db

@measure_time
def inicializar_db_wrapper():
    """
    Función wrapper para inicializar la base de datos.
    Proporciona manejo de errores adicional.
    
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """
    try:
        # Verificar que el directorio model existe
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(base_dir, 'model')
        
        if not os.path.exists(model_dir):
            os.makedirs(model_dir, exist_ok=True)
            logger.info(f"Directorio creado: {model_dir}")
            
        # Inicializar la base de datos
        inicializar_db()
        logger.info("Base de datos inicializada correctamente")
        return True
    except Exception as e:
        error_msg = f"Error al inicializar la base de datos: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        # Escribir el error en un archivo de log
        try:
            with open('error_log.txt', 'a') as f:
                f.write(f"{error_msg}\n\n")
        except:
            pass
            
        return False

@measure_time
def backup_database():
    """
    Realiza una copia de seguridad de la base de datos.
    
    Returns:
        bool: True si el backup fue exitoso, False en caso contrario
    """
    try:
        import shutil
        from datetime import datetime
        
        # Ruta de la base de datos usando os.path para compatibilidad
        db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finanzas.db')
        
        # Verificar que el archivo existe
        if not os.path.exists(db_file):
            logger.error(f"No se encontró la base de datos: {db_file}")
            return False
            
        # Crear nombre de archivo para el backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f'finanzas_backup_{timestamp}.db'
        
        # Crear directorio de backups si no existe
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
            
        backup_path = os.path.join(backup_dir, backup_file)
        
        # Copiar el archivo
        shutil.copy2(db_file, backup_path)
        logger.info(f"Base de datos respaldada en: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Error al crear backup: {e}")
        return False

def cerrar_conexiones_db():
    """
    Cierra todas las conexiones abiertas a la base de datos
    al salir de la aplicación.
    """
    try:
        # Intentar cerrar la conexión del pool
        if 'DBConnectionManager' in globals():
            DBConnectionManager.get_instance().close_connection()
            logger.info("Conexiones a la base de datos cerradas correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al cerrar conexiones a la base de datos: {e}")
        return False
    
# Agregar a utils.py
class ThreadManager:
    """Clase para gestionar hilos de manera segura"""
    active_threads = []
    
    @classmethod
    def create_thread(cls, target, args=(), kwargs=None, daemon=True):
        """Crea un hilo y lo guarda en la lista de hilos activos"""
        if kwargs is None:
            kwargs = {}
            
        thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=daemon)
        cls.active_threads.append(thread)
        thread.start()
        return thread
    
    @classmethod
    def cleanup_threads(cls):
        """Limpia la lista de hilos inactivos"""
        cls.active_threads = [t for t in cls.active_threads if t.is_alive()]
        
    @classmethod
    def join_all(cls, timeout=None):
        """Espera a que todos los hilos terminen"""
        for thread in cls.active_threads:
            try:
                if thread.is_alive():
                    thread.join(timeout=timeout)
            except Exception as e:
                logger.error(f"Error al esperar hilo: {e}")