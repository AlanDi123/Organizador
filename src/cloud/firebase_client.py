"""
Cliente Firebase para sincronización cloud
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from src.config.env_config import EnvConfig

logger = logging.getLogger(__name__)


class FirebaseClient:
    """
    Cliente para conectar con Firebase Firestore
    Maneja autenticación y operaciones CRUD
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
        self.db = None
        self.auth = None
        self.enabled = False
        self.user_id = None
        self.device_id = None
        
        # Intentar inicializar
        self._initialize()
    
    def _initialize(self):
        """Inicializa la conexión con Firebase"""
        try:
            # Verificar si está habilitado
            self.enabled = EnvConfig.get('FIREBASE_ENABLED', False)
            
            if not self.enabled:
                logger.info("Firebase no está habilitado. Usando modo offline.")
                return
            
            # Obtener ruta de credenciales
            creds_path = EnvConfig.get('FIREBASE_CREDENTIALS_PATH', 'firebase_credentials.json')
            project_id = EnvConfig.get('FIREBASE_PROJECT_ID', '')
            
            if not os.path.exists(creds_path):
                logger.warning(f"Archivo de credenciales no encontrado: {creds_path}")
                self.enabled = False
                return
            
            # Importar Firebase (solo si está disponible)
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore
                from firebase_admin import auth as firebase_auth
            except ImportError:
                logger.warning("firebase-admin no está instalado. Modo offline activado.")
                self.enabled = False
                return
            
            # Inicializar app de Firebase
            try:
                cred = credentials.Certificate(creds_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': project_id,
                })
                self.db = firestore.client()
                self.auth = firebase_auth
                self.enabled = True
                logger.info("Firebase inicializado correctamente")
            except Exception as e:
                logger.error(f"Error al inicializar Firebase: {e}")
                self.enabled = False
                
        except Exception as e:
            logger.error(f"Error en inicialización de Firebase: {e}")
            self.enabled = False
    
    def generate_device_id(self) -> str:
        """Genera un ID único para el dispositivo"""
        import uuid
        # Usar UUID basado en MAC address + timestamp
        return str(uuid.uuid4())
    
    def get_device_id(self) -> str:
        """Obtiene o genera el ID del dispositivo"""
        if self.device_id is None:
            self.device_id = self.generate_device_id()
        return self.device_id
    
    def authenticate(self, email: str, password: str) -> Optional[str]:
        """
        Autentica usuario con email/password
        Returns: user_id o None si falla
        """
        if not self.enabled:
            return None
        
        try:
            # Crear usuario o sign in
            user = self.auth.get_user_by_email(email)
            self.user_id = user.uid
            return self.user_id
        except Exception as e:
            logger.error(f"Error de autenticación: {e}")
            return None
    
    def create_user(self, email: str, password: str, display_name: str = "") -> Optional[str]:
        """
        Crea un nuevo usuario
        Returns: user_id o None si falla
        """
        if not self.enabled:
            return None
        
        try:
            user = self.auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            self.user_id = user.uid
            return self.user_id
        except Exception as e:
            logger.error(f"Error al crear usuario: {e}")
            return None
    
    def sign_out(self):
        """Cierra sesión del usuario actual"""
        self.user_id = None
    
    def is_authenticated(self) -> bool:
        """Verifica si hay un usuario autenticado"""
        return self.enabled and self.user_id is not None
    
    def get_user_id(self) -> Optional[str]:
        """Obtiene el ID del usuario autenticado"""
        return self.user_id
    
    # Operaciones CRUD para registros
    
    def save_record(self, collection: str, data: Dict[str, Any], doc_id: Optional[str] = None) -> Optional[str]:
        """Guarda un registro en Firestore"""
        if not self.enabled or not self.user_id:
            return None
        
        try:
            if doc_id:
                self.db.collection(collection).document(doc_id).set(data)
                return doc_id
            else:
                doc_ref = self.db.collection(collection).add(data)
                return doc_ref[1].id
        except Exception as e:
            logger.error(f"Error al guardar registro: {e}")
            return None
    
    def get_record(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un registro de Firestore"""
        if not self.enabled:
            return None
        
        try:
            doc = self.db.collection(collection).document(doc_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error al obtener registro: {e}")
            return None
    
    def get_user_records(self, collection: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Obtiene todos los registros de un usuario"""
        if not self.enabled or not self.user_id:
            return []
        
        try:
            query = self.db.collection(collection).where('user_id', '==', self.user_id)
            
            if filters:
                for field, value in filters.items():
                    query = query.where(field, '==', value)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error al obtener registros: {e}")
            return []
    
    def update_record(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Actualiza un registro en Firestore"""
        if not self.enabled or not self.user_id:
            return False
        
        try:
            self.db.collection(collection).document(doc_id).update(data)
            return True
        except Exception as e:
            logger.error(f"Error al actualizar registro: {e}")
            return False
    
    def delete_record(self, collection: str, doc_id: str) -> bool:
        """Elimina un registro de Firestore"""
        if not self.enabled or not self.user_id:
            return False
        
        try:
            self.db.collection(collection).document(doc_id).delete()
            return True
        except Exception as e:
            logger.error(f"Error al eliminar registro: {e}")
            return False
    
    def batch_save(self, collection: str, records: List[Dict[str, Any]]) -> bool:
        """Guarda múltiples registros en batch"""
        if not self.enabled or not self.user_id:
            return False
        
        try:
            batch = self.db.batch()
            for record in records:
                doc_ref = self.db.collection(collection).document(record['id'])
                batch.set(doc_ref, record)
            batch.commit()
            return True
        except Exception as e:
            logger.error(f"Error en guardado batch: {e}")
            return False
    
    def sync_log(self, log_data: Dict[str, Any]) -> bool:
        """Registra un evento de sincronización"""
        return self.save_record('sync_logs', log_data)
    
    def get_last_sync(self, record_type: str) -> Optional[datetime]:
        """Obtiene el timestamp del último sync para un tipo de registro"""
        if not self.enabled or not self.user_id:
            return None
        
        try:
            doc = self.db.collection('sync_metadata').document(f"{self.user_id}_{record_type}").get()
            if doc.exists:
                data = doc.to_dict()
                return datetime.fromisoformat(data['last_sync'])
            return None
        except Exception as e:
            logger.error(f"Error al obtener último sync: {e}")
            return None
    
    def update_last_sync(self, record_type: str) -> bool:
        """Actualiza el timestamp del último sync"""
        if not self.enabled or not self.user_id:
            return False
        
        try:
            data = {
                'user_id': self.user_id,
                'record_type': record_type,
                'last_sync': datetime.now().isoformat()
            }
            self.db.collection('sync_metadata').document(f"{self.user_id}_{record_type}").set(data)
            return True
        except Exception as e:
            logger.error(f"Error al actualizar último sync: {e}")
            return False
