"""
Motor de sincronización bidireccional
Maneja sync entre SQLite local y Firestore cloud
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from src.cloud.firebase_client import FirebaseClient
from src.cloud.models import CloudRecord, RecordType, SyncStatus, SyncLog
from src.models.data_manager import DBConnectionManager, DB_FILE

logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Motor de sincronización bidireccional
    - Sync local -> cloud (subir cambios locales)
    - Sync cloud -> local (bajar cambios remotos)
    - Resolución de conflictos (timestamp-based)
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.firebase = FirebaseClient()
        self.sync_queue = []
        self.is_syncing = False
        
        # Mapeo de tablas locales a colecciones cloud
        self.collection_map = {
            'gastos': 'gastos',
            'ingresos': 'ingresos',
            'presupuesto': 'presupuesto'
        }
    
    def sync_all(self) -> Dict[str, int]:
        """
        Ejecuta sincronización completa
        Returns: dict con cantidad de registros sync por tabla
        """
        if not self.firebase.enabled:
            logger.info("Sync deshabilitado. Usando modo offline.")
            return {}
        
        if not self.firebase.is_authenticated():
            logger.warning("No hay usuario autenticado. Sync omitido.")
            return {}
        
        if self.is_syncing:
            logger.warning("Sync ya está en progreso.")
            return {}
        
        self.is_syncing = True
        results = {'uploaded': 0, 'downloaded': 0, 'conflicts': 0, 'errors': 0}
        
        try:
            # 1. Subir cambios locales pendientes
            upload_result = self._sync_local_to_cloud()
            results['uploaded'] = upload_result.get('count', 0)
            results['conflicts'] += upload_result.get('conflicts', 0)
            
            # 2. Bajar cambios remotos
            download_result = self._sync_cloud_to_local()
            results['downloaded'] = download_result.get('count', 0)
            results['conflicts'] += download_result.get('conflicts', 0)
            
            # 3. Actualizar metadata
            self._update_sync_metadata()
            
            logger.info(f"Sync completado: {results}")
            
        except Exception as e:
            logger.error(f"Error en sync: {e}")
            results['errors'] += 1
        finally:
            self.is_syncing = False
        
        return results
    
    def _sync_local_to_cloud(self) -> Dict[str, Any]:
        """Sincroniza cambios locales hacia la nube"""
        result = {'count': 0, 'conflicts': 0, 'errors': 0}
        
        try:
            conn = DBConnectionManager.get_instance().get_connection()
            cursor = conn.cursor()
            
            # Verificar si existe la tabla sync_metadata
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_metadata'")
            if not cursor.fetchone():
                logger.info("Tabla sync_metadata no existe. Creando...")
                cursor.execute('''
                    CREATE TABLE sync_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        record_id TEXT,
                        record_type TEXT,
                        last_sync TEXT,
                        sync_status TEXT DEFAULT 'pending'
                    )
                ''')
                conn.commit()
            
            # Obtener registros locales modificados desde último sync
            for local_table, cloud_collection in self.collection_map.items():
                records = self._get_pending_local_records(local_table)
                
                for record in records:
                    try:
                        # Crear registro cloud
                        cloud_record = self._local_to_cloud_record(record, local_table)
                        
                        # Verificar conflictos
                        if self._has_conflict(cloud_record, cloud_collection):
                            result['conflicts'] += 1
                            # Resolver conflicto (último timestamp gana)
                            if not self._resolve_conflict(cloud_record, cloud_collection):
                                continue
                        
                        # Guardar en cloud
                        doc_id = self.firebase.save_record(cloud_collection, cloud_record.to_firestore(), cloud_record.id)
                        
                        if doc_id:
                            result['count'] += 1
                            self._mark_as_synced(local_table, record['id'])
                            
                            # Log sync
                            self._log_sync('upload', local_table, record['id'], True)
                        else:
                            result['errors'] += 1
                            self._log_sync('upload', local_table, record['id'], False, 'Failed to save to cloud')
                    
                    except Exception as e:
                        logger.error(f"Error al sync registro {local_table}/{record['id']}: {e}")
                        result['errors'] += 1
            
        except Exception as e:
            logger.error(f"Error en sync local->cloud: {e}")
        
        return result
    
    def _sync_cloud_to_local(self) -> Dict[str, Any]:
        """Sincroniza cambios desde la nube hacia local"""
        result = {'count': 0, 'conflicts': 0, 'errors': 0}
        
        try:
            for local_table, cloud_collection in self.collection_map.items():
                # Obtener registros cloud
                cloud_records = self.firebase.get_user_records(cloud_collection)
                
                for cloud_data in cloud_records:
                    try:
                        cloud_record = CloudRecord.from_firestore(cloud_data)
                        
                        # Verificar si existe localmente
                        local_record = self._get_local_record(local_table, cloud_record.id)
                        
                        if local_record is None:
                            # Nuevo registro, insertar
                            self._insert_local_record(local_table, cloud_record)
                            result['count'] += 1
                        else:
                            # Existe, verificar conflicto
                            if self._has_local_changes(local_table, local_record, cloud_record):
                                result['conflicts'] += 1
                                # Resolver conflicto
                                if self._resolve_conflict_in_favor(cloud_record, local_table):
                                    self._update_local_record(local_table, cloud_record)
                                    result['count'] += 1
                            # Si no hay cambios locales, no hacer nada (ya está sync)
                    
                    except Exception as e:
                        logger.error(f"Error al sync cloud->local {cloud_data.get('id')}: {e}")
                        result['errors'] += 1
        
        except Exception as e:
            logger.error(f"Error en sync cloud->local: {e}")
        
        return result
    
    def _get_pending_local_records(self, table: str) -> List[Dict[str, Any]]:
        """Obtiene registros locales pendientes de sync"""
        try:
            conn = DBConnectionManager.get_instance().get_connection()
            cursor = conn.cursor()
            
            # Obtener último sync timestamp
            cursor.execute('''
                SELECT last_sync FROM sync_metadata 
                WHERE record_type = ? 
                ORDER BY last_sync DESC LIMIT 1
            ''', (table,))
            
            row = cursor.fetchone()
            if row:
                last_sync = row[0]
                # Obtener registros modificados después del último sync
                cursor.execute(f'''
                    SELECT * FROM {table}
                    WHERE fecha_creacion > ? OR fecha_creacion IS NULL
                ''', (last_sync,))
            else:
                # No hay sync previo, obtener todos
                cursor.execute(f'SELECT * FROM {table}')
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error al obtener registros pendientes: {e}")
            return []
    
    def _local_to_cloud_record(self, local_data: Dict[str, Any], table: str) -> CloudRecord:
        """Convierte registro local a formato cloud"""
        record_type_map = {
            'gastos': RecordType.GASTO,
            'ingresos': RecordType.INGRESO,
            'presupuesto': RecordType.PRESUPUESTO
        }
        
        return CloudRecord(
            id=str(local_data.get('id', '')),
            record_type=record_type_map.get(table, RecordType.GASTO),
            user_id=self.firebase.get_user_id() or '',
            data=local_data,
            timestamp=datetime.now(),
            device_id=self.firebase.get_device_id()
        )
    
    def _get_local_record(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un registro local por ID"""
        try:
            conn = DBConnectionManager.get_instance().get_connection()
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM {table} WHERE id = ?', (record_id,))
            
            if cursor.rowcount == 0:
                return None
            
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, cursor.fetchone()))
            
        except Exception as e:
            logger.error(f"Error al obtener registro local: {e}")
            return None
    
    def _insert_local_record(self, table: str, cloud_record: CloudRecord):
        """Inserta registro cloud en DB local"""
        try:
            conn = DBConnectionManager.get_instance().get_connection()
            cursor = conn.cursor()
            
            # Extraer datos del record
            data = cloud_record.data
            columns = list(data.keys())
            values = list(data.values())
            
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns)
            
            cursor.execute(f'''
                INSERT OR REPLACE INTO {table} ({columns_str})
                VALUES ({placeholders})
            ''', values)
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error al insertar registro local: {e}")
    
    def _update_local_record(self, table: str, cloud_record: CloudRecord):
        """Actualiza registro local desde cloud"""
        try:
            conn = DBConnectionManager.get_instance().get_connection()
            cursor = conn.cursor()
            
            data = cloud_record.data
            record_id = data.get('id')
            
            if not record_id:
                return
            
            # Construir UPDATE dinámico
            set_clause = ', '.join([f'{col} = ?' for col in data.keys() if col != 'id'])
            values = list(data.values())
            
            cursor.execute(f'''
                UPDATE {table} SET {set_clause}
                WHERE id = ?
            ''', values)
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error al actualizar registro local: {e}")
    
    def _has_conflict(self, cloud_record: CloudRecord, collection: str) -> bool:
        """Verifica si hay conflicto en cloud"""
        # Implementación simplificada: siempre retorna False
        # En producción, comparar timestamps
        return False
    
    def _resolve_conflict(self, cloud_record: CloudRecord, collection: str) -> bool:
        """Resuelve conflicto a favor del cloud (último timestamp)"""
        # Obtener registro cloud existente
        existing = self.firebase.get_record(collection, cloud_record.id)
        
        if existing:
            existing_time = datetime.fromisoformat(existing['timestamp'])
            if cloud_record.timestamp > existing_time:
                # El nuevo es más reciente, actualizar
                return self.firebase.update_record(collection, cloud_record.id, cloud_record.to_firestore())
            return False
        return True
    
    def _has_local_changes(self, table: str, local: Dict, cloud: CloudRecord) -> bool:
        """Verifica si hay cambios locales no sincronizados"""
        # Comparar timestamps
        local_time = local.get('fecha_creacion', '')
        cloud_time = cloud.data.get('fecha_creacion', '')
        return local_time != cloud_time
    
    def _resolve_conflict_in_favor(self, cloud_record: CloudRecord, table: str) -> bool:
        """Resuelve conflicto a favor del cloud"""
        # En producción, implementar lógica más sofisticada
        # Por ahora, cloud siempre gana
        return True
    
    def _mark_as_synced(self, table: str, record_id: str):
        """Marca un registro como sincronizado"""
        try:
            conn = DBConnectionManager.get_instance().get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO sync_metadata (record_id, record_type, last_sync, sync_status)
                VALUES (?, ?, ?, ?)
            ''', (record_id, table, datetime.now().isoformat(), 'synced'))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error al marcar como sync: {e}")
    
    def _update_sync_metadata(self):
        """Actualiza metadata de sincronización"""
        for table in self.collection_map.keys():
            self.firebase.update_last_sync(table)
    
    def _log_sync(self, action: str, record_type: str, record_id: str, success: bool, error: str = None):
        """Registra evento de sincronización"""
        log = SyncLog(
            user_id=self.firebase.get_user_id() or '',
            record_id=record_id,
            record_type=record_type,
            action=action,
            success=success,
            error_message=error
        )
        self.firebase.sync_log(log.to_firestore())
    
    def force_sync(self):
        """Fuerza sincronización inmediata"""
        logger.info("Forzando sincronización...")
        return self.sync_all()
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Obtiene estado actual de sincronización"""
        return {
            'enabled': self.firebase.enabled,
            'authenticated': self.firebase.is_authenticated(),
            'user_id': self.firebase.get_user_id(),
            'is_syncing': self.is_syncing,
            'last_sync': self.firebase.get_last_sync('gastos')  # Ejemplo
        }
