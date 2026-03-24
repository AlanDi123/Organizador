"""
Cliente Firebase REST para sincronización cloud
Usa Auth REST + Firestore REST API (sin Admin SDK - compatible con APK)
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

import requests

from src.config.env_config import EnvConfig

logger = logging.getLogger(__name__)


class FirebaseClient:
    """
    Cliente para conectar con Firebase Firestore usando REST API
    Compatible con Android APK (sin dependencias de servidor)
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
        self.enabled = False
        self.user_id = None
        self.id_token = None
        self.refresh_token = None
        self.expires_at = None
        self.device_id = None

        # Config desde variables de entorno
        self.api_key = EnvConfig.get('FIREBASE_WEB_API_KEY', '')
        self.project_id = EnvConfig.get('FIREBASE_PROJECT_ID', '')
        
        # Verificar si está habilitado
        self.enabled = EnvConfig.get('FIREBASE_ENABLED', False) and bool(self.api_key) and bool(self.project_id)

        if not self.enabled:
            logger.info("Firebase no está habilitado o faltan credenciales. Usando modo offline.")

    def generate_device_id(self) -> str:
        """Genera un ID único para el dispositivo"""
        import uuid
        return str(uuid.uuid4())

    def get_device_id(self) -> str:
        """Obtiene o genera el ID del dispositivo"""
        if self.device_id is None:
            self.device_id = self.generate_device_id()
        return self.device_id

    def _headers(self) -> dict:
        """Headers para requests a Firestore REST"""
        return {
            "Authorization": f"Bearer {self.id_token}",
            "Content-Type": "application/json"
        }

    def authenticate(self, email: str, password: str) -> Optional[str]:
        """
        Autentica usuario con email/password usando Auth REST
        Returns: user_id o None si falla
        """
        if not self.api_key:
            return None

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            r = requests.post(url, json=payload, timeout=15)
            r.raise_for_status()
            data = r.json()

            self.user_id = data["localId"]
            self.id_token = data["idToken"]
            self.refresh_token = data["refreshToken"]
            
            # Calcular expiry (el token dura ~1 hora)
            expires_in = int(data.get("expiresIn", 3600))
            from datetime import timedelta
            self.expires_at = datetime.now() + timedelta(seconds=expires_in) - timedelta(minutes=5)
            
            logger.info(f"Usuario autenticado: {self.user_id}")
            return self.user_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de autenticación: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error de autenticación: {e}")
            return None

    def create_user(self, email: str, password: str, display_name: str = "") -> Optional[str]:
        """
        Crea un nuevo usuario usando Auth REST
        Returns: user_id o None si falla
        """
        if not self.api_key:
            return None

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            r = requests.post(url, json=payload, timeout=15)
            r.raise_for_status()
            data = r.json()

            self.user_id = data["localId"]
            self.id_token = data["idToken"]
            self.refresh_token = data["refreshToken"]
            
            from datetime import timedelta
            expires_in = int(data.get("expiresIn", 3600))
            self.expires_at = datetime.now() + timedelta(seconds=expires_in) - timedelta(minutes=5)
            
            logger.info(f"Usuario creado: {self.user_id}")
            return self.user_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al crear usuario: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error al crear usuario: {e}")
            return None

    def sign_out(self):
        """Cierra sesión del usuario actual"""
        self.user_id = None
        self.id_token = None
        self.refresh_token = None
        self.expires_at = None

    def is_authenticated(self) -> bool:
        """Verifica si hay un usuario autenticado con token válido"""
        if not self.enabled or not self.user_id or not self.id_token:
            return False
        
        # Verificar si el token expiró
        if self.expires_at and datetime.now() >= self.expires_at:
            logger.info("Token expirado, requiere re-autenticación")
            return False
            
        return True

    def get_user_id(self) -> Optional[str]:
        """Obtiene el ID del usuario autenticado"""
        return self.user_id

    # Operaciones CRUD para Firestore REST

    def _get_firestore_url(self, collection: str, doc_id: Optional[str] = None) -> str:
        """Construye URL para Firestore REST"""
        base = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"
        if doc_id:
            return f"{base}/{collection}/{doc_id}"
        return f"{base}/{collection}"

    def _to_firestore_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte dict Python a formato Firestore REST"""
        result = {}
        for key, value in data.items():
            if value is None:
                result[key] = {"nullValue": None}
            elif isinstance(value, bool):
                result[key] = {"booleanValue": value}
            elif isinstance(value, int):
                result[key] = {"integerValue": value}
            elif isinstance(value, float):
                result[key] = {"doubleValue": value}
            elif isinstance(value, str):
                result[key] = {"stringValue": value}
            elif isinstance(value, datetime):
                result[key] = {"timestampValue": value.isoformat() + "Z"}
            elif isinstance(value, list):
                result[key] = {"arrayValue": {"values": [self._to_firestore_format({str(i): v})[str(i)] for i, v in enumerate(value)]}}
            elif isinstance(value, dict):
                result[key] = {"mapValue": {"fields": self._to_firestore_format(value)}}
            else:
                result[key] = {"stringValue": str(value)}
        return result

    def _from_firestore_format(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte formato Firestore REST a dict Python"""
        if not fields:
            return {}
        
        result = {}
        for key, value in fields.items():
            if "stringValue" in value:
                result[key] = value["stringValue"]
            elif "integerValue" in value:
                result[key] = int(value["integerValue"])
            elif "doubleValue" in value:
                result[key] = float(value["doubleValue"])
            elif "booleanValue" in value:
                result[key] = value["booleanValue"]
            elif "timestampValue" in value:
                ts = value["timestampValue"].rstrip("Z")
                try:
                    result[key] = datetime.fromisoformat(ts)
                except:
                    result[key] = value["timestampValue"]
            elif "nullValue" in value:
                result[key] = None
            elif "arrayValue" in value:
                arr = value["arrayValue"].get("values", [])
                result[key] = [self._from_firestore_format({"_": v})["_"] for v in arr]
            elif "mapValue" in value:
                result[key] = self._from_firestore_format(value["mapValue"].get("fields", {}))
        return result

    def save_record(self, collection: str, data: Dict[str, Any], doc_id: Optional[str] = None) -> Optional[str]:
        """Guarda un registro en Firestore usando REST"""
        if not self.enabled or not self.is_authenticated():
            return None

        try:
            url = self._get_firestore_url(collection, doc_id)
            firestore_data = self._to_firestore_format(data)
            
            # Usar PATCH para actualizar/crear, PUT para forzar creación
            method = "patch" if doc_id else "post"
            if doc_id:
                url += "?currentDocument.exists=true"
            
            r = requests.request(method, url, json={"fields": firestore_data}, headers=self._headers(), timeout=15)
            
            if r.status_code not in [200, 201]:
                logger.error(f"Error al guardar: {r.text}")
                return None
            
            response_data = r.json()
            # Extraer doc_id de la respuesta (nombre del recurso)
            name = response_data.get("name", "")
            saved_id = name.split("/")[-1] if name else doc_id
            return saved_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al guardar registro: {e}")
            return None
        except Exception as e:
            logger.error(f"Error al guardar registro: {e}")
            return None

    def get_record(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un registro de Firestore usando REST"""
        if not self.enabled or not self.is_authenticated():
            return None

        try:
            url = self._get_firestore_url(collection, doc_id)
            r = requests.get(url, headers=self._headers(), timeout=15)
            
            if r.status_code == 404:
                return None
            
            r.raise_for_status()
            data = r.json()
            return self._from_firestore_format(data.get("fields", {}))

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener registro: {e}")
            return None
        except Exception as e:
            logger.error(f"Error al obtener registro: {e}")
            return None

    def get_user_records(self, collection: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Obtiene todos los registros de un usuario usando Firestore REST query"""
        if not self.enabled or not self.is_authenticated():
            return []

        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/{collection}:runQuery"

            # Fix 5: Construir query con filtros - formato correcto para Firestore REST API
            structured_query = {
                "from": [{"collectionId": collection}],
                "where": {
                    "fieldFilter": {  # Fix 5: wrapper requerido
                        "field": {"fieldPath": "user_id"},
                        "op": "EQUAL",
                        "value": {"stringValue": self.user_id}
                    }
                }
            }

            # Agregar filtros adicionales
            if filters:
                composite_filters = []
                composite_filters.append({
                    "fieldFilter": {  # Fix 5: wrapper fieldFilter
                        "field": {"fieldPath": "user_id"},
                        "op": "EQUAL",
                        "value": {"stringValue": self.user_id}
                    }
                })
                for field, value in filters.items():
                    composite_filters.append({
                        "fieldFilter": {  # Fix 5: wrapper fieldFilter
                            "field": {"fieldPath": field},
                            "op": "EQUAL",
                            "value": {"stringValue": str(value)} if not isinstance(value, bool) else {"booleanValue": value}
                        }
                    })

                structured_query["where"] = {
                    "compositeFilter": {  # Fix 5: wrapper compositeFilter
                        "op": "AND",
                        "filters": composite_filters
                    }
                }

            r = requests.post(url, json={"structuredQuery": structured_query}, headers=self._headers(), timeout=15)
            r.raise_for_status()

            data = r.json()
            results = []
            for doc in data:
                if "document" in doc:
                    fields = doc["document"].get("fields", {})
                    record = self._from_firestore_format(fields)
                    # Extraer ID del documento
                    name = doc["document"].get("name", "")
                    record["doc_id"] = name.split("/")[-1] if name else None
                    results.append(record)

            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener registros: {e}")
            return []
        except Exception as e:
            logger.error(f"Error al obtener registros: {e}")
            return []

    def update_record(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Actualiza un registro en Firestore usando REST"""
        if not self.enabled or not self.is_authenticated():
            return False

        try:
            url = self._get_firestore_url(collection, doc_id)
            firestore_data = self._to_firestore_format(data)

            # Fix 13: PATCH con mask - Firestore REST usa updateMask.fieldPaths como lista
            mask_paths = list(data.keys())
            params = [("updateMask.fieldPaths", field) for field in mask_paths]
            r = requests.patch(
                url,
                json={"fields": firestore_data},
                headers=self._headers(),
                params=params,
                timeout=15
            )
            r.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al actualizar registro: {e}")
            return False
        except Exception as e:
            logger.error(f"Error al actualizar registro: {e}")
            return False

    def delete_record(self, collection: str, doc_id: str) -> bool:
        """Elimina un registro de Firestore usando REST"""
        if not self.enabled or not self.is_authenticated():
            return False

        try:
            url = self._get_firestore_url(collection, doc_id)
            r = requests.delete(url, headers=self._headers(), timeout=15)
            r.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al eliminar registro: {e}")
            return False
        except Exception as e:
            logger.error(f"Error al eliminar registro: {e}")
            return False

    def batch_save(self, collection: str, records: List[Dict[str, Any]]) -> bool:
        """Guarda múltiples registros en batch usando Firestore REST batchWrite"""
        if not self.enabled or not self.is_authenticated():
            return False

        try:
            url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents:batchWrite"
            
            writes = []
            for record in records:
                doc_id = record.get("id") or record.get("uuid")
                if not doc_id:
                    continue
                    
                firestore_data = self._to_firestore_format(record)
                writes.append({
                    "update": {
                        "name": f"projects/{self.project_id}/databases/(default)/documents/{collection}/{doc_id}",
                        "fields": firestore_data
                    }
                })

            r = requests.post(url, json={"writes": writes}, headers=self._headers(), timeout=30)
            r.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error en guardado batch: {e}")
            return False
        except Exception as e:
            logger.error(f"Error en guardado batch: {e}")
            return False

    def sync_log(self, log_data: Dict[str, Any]) -> bool:
        """Registra un evento de sincronización"""
        return self.save_record('sync_logs', log_data)

    def get_last_sync(self, record_type: str) -> Optional[datetime]:
        """Obtiene el timestamp del último sync para un tipo de registro"""
        if not self.enabled or not self.is_authenticated():
            return None

        try:
            doc_id = f"{self.user_id}_{record_type}"
            doc = self.get_record('sync_metadata', doc_id)
            
            if doc and 'last_sync' in doc:
                last_sync = doc['last_sync']
                if isinstance(last_sync, str):
                    return datetime.fromisoformat(last_sync.rstrip("Z"))
                return last_sync
            return None

        except Exception as e:
            logger.error(f"Error al obtener último sync: {e}")
            return None

    def update_last_sync(self, record_type: str) -> bool:
        """Actualiza el timestamp del último sync"""
        if not self.enabled or not self.is_authenticated():
            return False

        try:
            doc_id = f"{self.user_id}_{record_type}"
            data = {
                'user_id': self.user_id,
                'record_type': record_type,
                'last_sync': datetime.now().isoformat()
            }
            return self.save_record('sync_metadata', data, doc_id)

        except Exception as e:
            logger.error(f"Error al actualizar último sync: {e}")
            return False
