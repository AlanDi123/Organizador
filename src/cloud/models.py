"""
Modelos de datos para sincronización cloud
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class SyncStatus(Enum):
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    ERROR = "error"


class RecordType(Enum):
    GASTO = "gasto"
    INGRESO = "ingreso"
    PRESUPUESTO = "presupuesto"
    USER = "user"


@dataclass
class CloudRecord:
    """Representa un registro para sincronizar con la nube"""
    id: str
    record_type: RecordType
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime
    device_id: str
    sync_status: SyncStatus = SyncStatus.PENDING
    version: int = 1
    
    def to_firestore(self) -> Dict[str, Any]:
        """Convierte a formato Firestore"""
        return {
            'id': self.id,
            'record_type': self.record_type.value,
            'user_id': self.user_id,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'device_id': self.device_id,
            'sync_status': self.sync_status.value,
            'version': self.version,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    @classmethod
    def from_firestore(cls, doc: Dict[str, Any]) -> 'CloudRecord':
        """Crea instancia desde documento Firestore"""
        return cls(
            id=doc['id'],
            record_type=RecordType(doc['record_type']),
            user_id=doc['user_id'],
            data=doc['data'],
            timestamp=datetime.fromisoformat(doc['timestamp']),
            device_id=doc['device_id'],
            sync_status=SyncStatus(doc.get('sync_status', 'pending')),
            version=doc.get('version', 1)
        )


@dataclass
class SyncLog:
    """Registro de auditoría para sincronización"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    record_id: str = ""
    record_type: str = ""
    action: str = ""  # create, update, delete
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None
    
    def to_firestore(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'record_id': self.record_id,
            'record_type': self.record_type,
            'action': self.action,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'error_message': self.error_message
        }


@dataclass
class UserDevice:
    """Dispositivo registrado para sync"""
    id: str
    user_id: str
    device_name: str
    platform: str  # android, ios, windows, linux, mac
    last_sync: datetime
    app_version: str
    
    def to_firestore(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_name': self.device_name,
            'platform': self.platform,
            'last_sync': self.last_sync.isoformat(),
            'app_version': self.app_version
        }
