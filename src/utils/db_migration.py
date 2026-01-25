# src/utils/db_migration.py
"""
Sistema automático de migración de base de datos con validación.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from src.utils.logger import get_logger
from src.utils.decorators import retry, timer

logger = get_logger(__name__)

# Ruta de la base de datos
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'finanzas.db')

# Versión actual del esquema
CURRENT_SCHEMA_VERSION = 2

@timer
@retry(max_attempts=3, delay=1.0)
def get_db_version() -> int:
    """Obtiene la versión actual de la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='version'")
        if cursor.fetchone() is None:
            conn.close()
            return 0
        
        cursor.execute("SELECT version FROM version")
        result = cursor.fetchone()
        version = result[0] if result else 0
        conn.close()
        
        return version
    except Exception as e:
        logger.error(f"Error al obtener versión de BD: {e}")
        return 0

@timer
def backup_database() -> Optional[str]:
    """Crea una copia de seguridad de la base de datos actual"""
    try:
        if not os.path.exists(DB_FILE):
            logger.warning("No existe base de datos para respaldar")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = os.path.join(backup_dir, f"finanzas_backup_{timestamp}.db")
        shutil.copy2(DB_FILE, backup_file)
        logger.info(f"✅ Base de datos respaldada en: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"❌ Error al crear backup: {e}")
        return None

def validate_database() -> bool:
    """Valida la integridad de la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        
        if result[0] == "ok":
            logger.info("✅ Base de datos íntegra")
            return True
        else:
            logger.error(f"❌ Problema en BD: {result}")
            return False
    except Exception as e:
        logger.error(f"Error validando BD: {e}")
        return False

def create_schema_v2(conn: sqlite3.Connection) -> bool:
    """Crea el esquema completo de versión 2"""
    cursor = conn.cursor()
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Crear tabla gastos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                es_historial BOOLEAN DEFAULT 0
            )
        """)
        
        # Crear tabla ingresos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingresos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concepto TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                es_historial BOOLEAN DEFAULT 0
            )
        """)
        
        # Crear tabla categorías
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT
            )
        """)
        
        # Crear tabla presupuesto
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuesto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                monto_limite REAL NOT NULL,
                categoria TEXT NOT NULL,
                mes TEXT,
                gasto_actual REAL DEFAULT 0
            )
        """)
        
        # Crear tabla versión
        cursor.execute("CREATE TABLE IF NOT EXISTS version (version INTEGER)")
        cursor.execute("INSERT OR IGNORE INTO version VALUES (2)")
        
        # Crear índices para optimización
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_nombre ON gastos(nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_historial ON gastos(es_historial)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_concepto ON ingresos(concepto)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_fecha ON ingresos(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_historial ON ingresos(es_historial)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_categorias_nombre ON categorias(nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_presupuesto_categoria ON presupuesto(categoria)')
        
        conn.commit()
        logger.info("✅ Esquema v2 creado exitosamente")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error al crear esquema v2: {e}")
        return False

def migrate_v0_to_v1(conn: sqlite3.Connection) -> bool:
    """Migra de la versión 0 a la versión 1"""
    cursor = conn.cursor()
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Verificar y agregar columnas
        try:
            cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE gastos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
            logger.info("Columna es_historial agregada a gastos")
        
        try:
            cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE ingresos ADD COLUMN es_historial BOOLEAN DEFAULT 0")
            logger.info("Columna es_historial agregada a ingresos")
        
        # Crear tabla versión e insertar versión 1
        cursor.execute("CREATE TABLE IF NOT EXISTS version (version INTEGER)")
        cursor.execute("INSERT OR IGNORE INTO version VALUES (1)")
        
        # Crear índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_nombre ON gastos(nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_concepto ON ingresos(concepto)')
        
        conn.commit()
        logger.info("✅ Migración de v0 a v1 completada")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error en migración v0 a v1: {e}")
        return False

def migrate_v1_to_v2(conn: sqlite3.Connection) -> bool:
    """Migra de la versión 1 a la versión 2"""
    cursor = conn.cursor()
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Agregar columnas si no existen
        try:
            cursor.execute("SELECT fecha_creacion FROM gastos LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE gastos ADD COLUMN fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP")
            logger.info("Columna fecha_creacion agregada a gastos")
        
        try:
            cursor.execute("SELECT fecha_creacion FROM ingresos LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE ingresos ADD COLUMN fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP")
            logger.info("Columna fecha_creacion agregada a ingresos")
        
        # Crear tablas que falta si no existen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presupuesto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                monto_limite REAL NOT NULL,
                categoria TEXT NOT NULL,
                mes TEXT,
                gasto_actual REAL DEFAULT 0
            )
        """)
        
        # Crear índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_historial ON gastos(es_historial)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_fecha ON ingresos(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_historial ON ingresos(es_historial)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_categorias_nombre ON categorias(nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_presupuesto_categoria ON presupuesto(categoria)')
        
        # Actualizar versión
        cursor.execute("UPDATE version SET version = 2")
        
        conn.commit()
        logger.info("✅ Migración de v1 a v2 completada")
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error en migración v1 a v2: {e}")
        return False

def run_migrations() -> bool:
    """Ejecuta todas las migraciones necesarias para actualizar la base de datos"""
    logger.info("🔄 Iniciando verificación de migraciones")
    
    # Si no existe BD, crearla desde cero con versión 2
    if not os.path.exists(DB_FILE):
        logger.info("ℹ️ No existe base de datos. Se creará con esquema v2...")
        try:
            conn = sqlite3.connect(DB_FILE)
            if not create_schema_v2(conn):
                conn.close()
                return False
            conn.close()
            logger.info(f"✅ Base de datos nueva creada con versión {CURRENT_SCHEMA_VERSION}")
            return True
        except Exception as e:
            logger.error(f"❌ Error creando BD nueva: {e}")
            return False
    
    # Si existe, validar integridad
    if not validate_database():
        logger.error("❌ Base de datos corrupta. Creando backup...")
        backup_database()
        return False
    
    # Crear backup antes de cualquier migración
    if not backup_database():
        logger.error("❌ No se pudo crear backup. Abortando migración.")
        return False
    
    # Obtener versión actual
    current_version = get_db_version()
    logger.info(f"📊 Versión actual de BD: {current_version}")
    
    # Si ya está actualizada, no hacer nada
    if current_version >= CURRENT_SCHEMA_VERSION:
        logger.info("✅ La base de datos ya está actualizada.")
        return True
    
    # Conectar y realizar migraciones
    try:
        conn = sqlite3.connect(DB_FILE)
        
        if current_version < 1:
            logger.info("🔄 Migrando de v0 a v1...")
            if not migrate_v0_to_v1(conn):
                conn.close()
                return False
                
        if current_version < 2:
            logger.info("🔄 Migrando de v1 a v2...")
            if not migrate_v1_to_v2(conn):
                conn.close()
                return False
        
        conn.close()
        logger.info(f"✅ Migración completada a versión {CURRENT_SCHEMA_VERSION}")
        return True
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        return False

def extract_data_from_old_version(old_db_path: str) -> Dict[str, List[Tuple]]:
    """Extrae datos de una versión anterior de la base de datos"""
    try:
        if not os.path.exists(old_db_path):
            logger.error(f"Base de datos antigua no encontrada: {old_db_path}")
            return {'gastos': [], 'ingresos': []}
        
        old_conn = sqlite3.connect(old_db_path)
        old_cursor = old_conn.cursor()
        
        data = {'gastos': [], 'ingresos': []}
        
        try:
            old_cursor.execute("SELECT * FROM gastos")
            data['gastos'] = [tuple(row) for row in old_cursor.fetchall()]
            logger.info(f"✅ Extraídos {len(data['gastos'])} gastos")
        except sqlite3.OperationalError as e:
            logger.warning(f"⚠️ No se pudo extraer gastos: {e}")
        
        try:
            old_cursor.execute("SELECT * FROM ingresos")
            data['ingresos'] = [tuple(row) for row in old_cursor.fetchall()]
            logger.info(f"✅ Extraídos {len(data['ingresos'])} ingresos")
        except sqlite3.OperationalError as e:
            logger.warning(f"⚠️ No se pudo extraer ingresos: {e}")
        
        old_conn.close()
        return data
    except Exception as e:
        logger.error(f"❌ Error al extraer datos: {e}")
        return {'gastos': [], 'ingresos': []}
