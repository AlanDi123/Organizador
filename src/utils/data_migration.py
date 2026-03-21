"""
Migración de datos - Compatibilidad con versiones anteriores
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class DataMigrator:
    """
    Migración de datos entre versiones
    - Mantiene compatibilidad con DB antiguas
    - Exporta/importa datos a formato cloud
    """
    
    def __init__(self, db_path: str = 'data/finanzas.db'):
        self.db_path = db_path
    
    def backup_before_migration(self) -> str:
        """Crea backup antes de migrar"""
        if not os.path.exists(self.db_path):
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data/finanzas_backup_migration_{timestamp}.db"
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Backup creado: {backup_path}")
        return backup_path
    
    def migrate_to_v3(self) -> bool:
        """
        Migra DB de versión 2.x a 3.x (con sync cloud)
        Añade columnas necesarias para sincronización
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar versión actual
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
            if cursor.fetchone():
                cursor.execute("SELECT version FROM schema_version")
                row = cursor.fetchone()
                current_version = row[0] if row else 1
            else:
                current_version = 1
            
            logger.info(f"Versión actual de schema: {current_version}")
            
            if current_version >= 3:
                logger.info("Schema ya está actualizado")
                conn.close()
                return True
            
            # Backup antes de migrar
            self.backup_before_migration()
            
            # Migración a v2: Añadir columnas de sync
            if current_version < 2:
                logger.info("Migrando a v2...")
                
                # Añadir columna sync_status a gastos
                try:
                    cursor.execute("ALTER TABLE gastos ADD COLUMN sync_status TEXT DEFAULT 'synced'")
                except sqlite3.OperationalError:
                    pass  # Ya existe
                
                # Añadir columna sync_status a ingresos
                try:
                    cursor.execute("ALTER TABLE ingresos ADD COLUMN sync_status TEXT DEFAULT 'synced'")
                except sqlite3.OperationalError:
                    pass
                
                # Añadir columna device_id
                try:
                    cursor.execute("ALTER TABLE gastos ADD COLUMN device_id TEXT")
                    cursor.execute("ALTER TABLE ingresos ADD COLUMN device_id TEXT")
                except sqlite3.OperationalError:
                    pass
            
            # Migración a v3: Añadir tablas de sync metadata
            if current_version < 3:
                logger.info("Migrando a v3...")
                
                # Tabla de sync_metadata
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sync_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        record_id TEXT,
                        record_type TEXT,
                        last_sync TEXT,
                        sync_status TEXT DEFAULT 'pending',
                        device_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabla de users (para auth local)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE,
                        password_hash TEXT,
                        display_name TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_sync TEXT
                    )
                ''')
                
                # Tabla de devices
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS devices (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        device_name TEXT,
                        platform TEXT,
                        app_version TEXT,
                        last_sync TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                ''')
                
                # Actualizar versión
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS schema_version (
                        id INTEGER PRIMARY KEY,
                        version INTEGER DEFAULT 1
                    )
                ''')
                cursor.execute("INSERT OR REPLACE INTO schema_version (id, version) VALUES (1, 3)")
            
            conn.commit()
            conn.close()
            
            logger.info("Migración completada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error en migración: {e}")
            return False
    
    def export_to_cloud_format(self, output_path: str = 'data/export_cloud.json') -> Dict[str, Any]:
        """
        Exporta datos locales a formato JSON para subir a cloud
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            data = {
                'version': 3,
                'export_date': datetime.now().isoformat(),
                'gastos': [],
                'ingresos': [],
                'presupuesto': []
            }
            
            # Exportar gastos
            cursor.execute("SELECT * FROM gastos WHERE es_historial = 0 OR es_historial IS NULL")
            for row in cursor.fetchall():
                data['gastos'].append(dict(row))
            
            # Exportar ingresos
            cursor.execute("SELECT * FROM ingresos WHERE es_historial = 0 OR es_historial IS NULL")
            for row in cursor.fetchall():
                data['ingresos'].append(dict(row))
            
            conn.close()
            
            # Guardar JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Datos exportados a: {output_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error al exportar: {e}")
            return {}
    
    def import_from_cloud_format(self, input_path: str) -> Dict[str, int]:
        """
        Importa datos desde formato cloud JSON a DB local
        Returns: cantidad de registros importados por tabla
        """
        try:
            # Leer JSON
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            results = {'gastos': 0, 'ingresos': 0, 'presupuesto': 0}
            
            # Importar gastos
            for gasto in data.get('gastos', []):
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO gastos 
                        (id, nombre, monto, recurrente, fecha, es_historial, fecha_creacion, sync_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        gasto.get('id'),
                        gasto.get('nombre'),
                        gasto.get('monto', 0),
                        gasto.get('recurrente', 0),
                        gasto.get('fecha'),
                        gasto.get('es_historial', 0),
                        gasto.get('fecha_creacion'),
                        'synced'
                    ))
                    results['gastos'] += 1
                except Exception as e:
                    logger.error(f"Error al importar gasto: {e}")
            
            # Importar ingresos
            for ingreso in data.get('ingresos', []):
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO ingresos 
                        (id, concepto, monto, fecha, es_historial, fecha_creacion, sync_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ingreso.get('id'),
                        ingreso.get('concepto'),
                        ingreso.get('monto', 0),
                        ingreso.get('fecha'),
                        ingreso.get('es_historial', 0),
                        ingreso.get('fecha_creacion'),
                        'synced'
                    ))
                    results['ingresos'] += 1
                except Exception as e:
                    logger.error(f"Error al importar ingreso: {e}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"Importación completada: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error al importar: {e}")
            return {'gastos': 0, 'ingresos': 0, 'presupuesto': 0}
    
    def merge_databases(self, old_db_path: str) -> Dict[str, int]:
        """
        Fusiona datos desde una DB antigua a la actual
        Evita duplicados por ID
        """
        try:
            if not os.path.exists(old_db_path):
                logger.error(f"DB antigua no existe: {old_db_path}")
                return {}
            
            conn_old = sqlite3.connect(old_db_path)
            conn_new = sqlite3.connect(self.db_path)
            
            cursor_old = conn_old.cursor()
            cursor_new = conn_new.cursor()
            
            results = {'gastos': 0, 'ingresos': 0}
            
            # Fusionar gastos
            cursor_old.execute("SELECT * FROM gastos WHERE es_historial = 0 OR es_historial IS NULL")
            gastos = cursor_old.fetchall()
            
            for gasto in gastos:
                # Verificar si ya existe
                cursor_new.execute("SELECT id FROM gastos WHERE id = ?", (gasto[0],))
                if not cursor_new.fetchone():
                    # Insertar si no existe
                    columns = len(gasto)
                    placeholders = ', '.join(['?' for _ in range(columns)])
                    cursor_new.execute(f'''
                        INSERT INTO gastos VALUES ({placeholders})
                    ''', gasto)
                    results['gastos'] += 1
            
            # Fusionar ingresos
            cursor_old.execute("SELECT * FROM ingresos WHERE es_historial = 0 OR es_historial IS NULL")
            ingresos = cursor_old.fetchall()
            
            for ingreso in ingresos:
                cursor_new.execute("SELECT id FROM ingresos WHERE id = ?", (ingreso[0],))
                if not cursor_new.fetchone():
                    columns = len(ingreso)
                    placeholders = ', '.join(['?' for _ in range(columns)])
                    cursor_new.execute(f'''
                        INSERT INTO ingresos VALUES ({placeholders})
                    ''', ingreso)
                    results['ingresos'] += 1
            
            conn_new.commit()
            conn_old.close()
            conn_new.close()
            
            logger.info(f"Fusión completada: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error en fusión: {e}")
            return {'gastos': 0, 'ingresos': 0}


def migrate_if_needed():
    """Ejecuta migración si es necesaria"""
    migrator = DataMigrator()
    return migrator.migrate_to_v3()


if __name__ == '__main__':
    # Ejecutar migración
    migrate_if_needed()
