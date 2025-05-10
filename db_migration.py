# model/db_migration.py
import sqlite3
import os
import shutil
import logging
from datetime import datetime
import json

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='migration.log'
)
logger = logging.getLogger('db_migration')

# Ruta de la base de datos
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'finanzas.db')

# Versión actual del esquema
CURRENT_SCHEMA_VERSION = 2  # Incrementa esto cada vez que modifiques el esquema

def get_db_version():
    """Obtiene la versión actual de la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si existe la tabla de versión
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='version'")
        if cursor.fetchone() is None:
            # La tabla no existe, es una versión antigua (pre-versionado)
            conn.close()
            return 0
        
        # Obtener la versión actual
        cursor.execute("SELECT version FROM version")
        version = cursor.fetchone()[0]
        conn.close()
        
        return version
    except Exception as e:
        logger.error(f"Error al obtener versión de BD: {e}")
        return 0  # Si hay error, asumir versión antigua

def backup_database():
    """Crea una copia de seguridad de la base de datos actual"""
    try:
        if not os.path.exists(DB_FILE):
            logger.warning("No existe base de datos para respaldar")
            return True
            
        # Crear nombre con timestamp para el backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = os.path.join(backup_dir, f"finanzas_backup_{timestamp}.db")
        
        # Copiar el archivo
        shutil.copy2(DB_FILE, backup_file)
        logger.info(f"Base de datos respaldada en: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Error al crear backup: {e}")
        return False

def migrate_v0_to_v1(conn):
    """Migra de la versión 0 (sin control de versiones) a la versión 1"""
    cursor = conn.cursor()
    
    try:
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # 1. Crear tabla de versión
        cursor.execute("CREATE TABLE IF NOT EXISTS version (version INTEGER)")
        cursor.execute("INSERT INTO version VALUES (1)")
        
        # 2. Verificar si gastos tiene columna es_historial
        try:
            cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            # No existe, agregarla
            cursor.execute("ALTER TABLE gastos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
            logger.info("Columna es_historial agregada a tabla gastos")
        
        # 3. Verificar si ingresos tiene columna es_historial
        try:
            cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            # No existe, agregarla
            cursor.execute("ALTER TABLE ingresos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
            logger.info("Columna es_historial agregada a tabla ingresos")
        
        # 4. Crear índices si no existen
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_nombre ON gastos(nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_concepto ON ingresos(concepto)')
        
        # Confirmar cambios
        conn.commit()
        logger.info("Migración de v0 a v1 completada")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en migración v0 a v1: {e}")
        return False

def migrate_v1_to_v2(conn):
    """Migra de la versión 1 a la versión 2"""
    cursor = conn.cursor()
    
    try:
        # Iniciar transacción
        conn.execute("BEGIN TRANSACTION")
        
        # 1. Actualizar versión
        cursor.execute("UPDATE version SET version = 2")
        
        # 2. Agregar columna fecha_creacion a gastos si no existe
        try:
            cursor.execute("SELECT fecha_creacion FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE gastos ADD COLUMN fecha_creacion TEXT")
            cursor.execute("UPDATE gastos SET fecha_creacion = datetime('now') WHERE fecha_creacion IS NULL")
            logger.info("Columna fecha_creacion agregada a tabla gastos")
        
        # 3. Agregar columna fecha_creacion a ingresos si no existe
        try:
            cursor.execute("SELECT fecha_creacion FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE ingresos ADD COLUMN fecha_creacion TEXT")
            cursor.execute("UPDATE ingresos SET fecha_creacion = datetime('now') WHERE fecha_creacion IS NULL")
            logger.info("Columna fecha_creacion agregada a tabla ingresos")
        
        # 4. Crear nuevos índices para optimización
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_fecha ON ingresos(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_historial ON gastos(es_historial)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_historial ON ingresos(es_historial)')
        
        # Confirmar cambios
        conn.commit()
        logger.info("Migración de v1 a v2 completada")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en migración v1 a v2: {e}")
        return False

def run_migrations():
    """Ejecuta todas las migraciones necesarias para actualizar la base de datos"""
    logger.info("Iniciando verificación de migraciones")
    
    # Verificar si existe la base de datos
    if not os.path.exists(DB_FILE):
        logger.info("No existe base de datos. Se creará con el esquema más reciente.")
        return True
    
    # Crear backup antes de cualquier migración
    if not backup_database():
        logger.error("No se pudo crear backup. Cancelando migración por seguridad.")
        return False
    
    # Obtener versión actual
    current_version = get_db_version()
    logger.info(f"Versión actual de la base de datos: {current_version}")
    
    # Si ya está actualizada, no hacer nada
    if current_version >= CURRENT_SCHEMA_VERSION:
        logger.info("La base de datos ya está actualizada.")
        return True
    
    # Conectar a la base de datos para las migraciones
    try:
        conn = sqlite3.connect(DB_FILE)
        
        # Migrar paso a paso
        if current_version < 1:
            if not migrate_v0_to_v1(conn):
                conn.close()
                return False
                
        if current_version < 2:
            if not migrate_v1_to_v2(conn):
                conn.close()
                return False
        
        # Aquí puedes agregar más migraciones en el futuro
        # if current_version < 3:
        #     migrate_v2_to_v3(conn)
        
        conn.close()
        logger.info(f"Migración completada a versión {CURRENT_SCHEMA_VERSION}")
        return True
    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        return False
    
def extract_data_from_old_version(old_db_path):
    """Extrae datos de una versión anterior de la base de datos"""
    import sqlite3
    import logging
    import os
    from datetime import datetime
    
    logger = logging.getLogger('db_migration')
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(old_db_path):
            logger.error(f"Base de datos antigua no encontrada: {old_db_path}")
            return None
            
        # Conectar a la base de datos antigua con una conexión independiente
        old_conn = sqlite3.connect(old_db_path)
        old_cursor = old_conn.cursor()
        
        # Inicializar diccionario de datos
        data = {'gastos': [], 'ingresos': []}
        
        # Extraer gastos
        try:
            old_cursor.execute("SELECT * FROM gastos")
            # Convertir filas a tuplas
            rows = old_cursor.fetchall()
            # Convertimos Row objects a listas y luego a tuplas para asegurar compatibilidad
            data['gastos'] = [tuple(row) for row in rows]
            logger.info(f"Extraídos {len(data['gastos'])} gastos")
        except sqlite3.OperationalError as e:
            logger.warning(f"No se pudo extraer gastos: {e}")
            data['gastos'] = []
        
        # Extraer ingresos
        try:
            old_cursor.execute("SELECT * FROM ingresos")
            # Convertir filas a tuplas
            rows = old_cursor.fetchall()
            # Convertimos Row objects a listas y luego a tuplas para asegurar compatibilidad
            data['ingresos'] = [tuple(row) for row in rows]
            logger.info(f"Extraídos {len(data['ingresos'])} ingresos")
        except sqlite3.OperationalError as e:
            logger.warning(f"No se pudo extraer ingresos: {e}")
            data['ingresos'] = []
            
        # Cerrar conexión
        old_conn.close()
        
        return data
    except Exception as e:
        logger.error(f"Error al extraer datos de versión antigua: {e}")
        # Devolver un diccionario vacío en lugar de None para evitar errores
        return {'gastos': [], 'ingresos': []}