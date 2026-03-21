"""
Tests para el módulo de sincronización cloud
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from src.cloud.models import CloudRecord, RecordType, SyncStatus, SyncLog, UserDevice
from src.cloud.firebase_client import FirebaseClient
from src.cloud.sync_engine import SyncEngine
from src.core.entities import Gasto, Ingreso, Presupuesto


class TestCloudModels(unittest.TestCase):
    """Tests para modelos de datos cloud"""
    
    def test_cloud_record_creation(self):
        """Test de creación de CloudRecord"""
        record = CloudRecord(
            id="test-123",
            record_type=RecordType.GASTO,
            user_id="user-456",
            data={'nombre': 'Test', 'monto': 100.0},
            timestamp=datetime.now(),
            device_id="device-789"
        )
        
        self.assertEqual(record.id, "test-123")
        self.assertEqual(record.record_type, RecordType.GASTO)
        self.assertEqual(record.sync_status, SyncStatus.PENDING)
        self.assertEqual(record.version, 1)
    
    def test_cloud_record_to_firestore(self):
        """Test de conversión a formato Firestore"""
        record = CloudRecord(
            id="test-123",
            record_type=RecordType.GASTO,
            user_id="user-456",
            data={'nombre': 'Test', 'monto': 100.0},
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            device_id="device-789"
        )
        
        firestore_data = record.to_firestore()
        
        self.assertEqual(firestore_data['id'], "test-123")
        self.assertEqual(firestore_data['record_type'], "gasto")
        self.assertEqual(firestore_data['user_id'], "user-456")
        self.assertIn('timestamp', firestore_data)
    
    def test_sync_log_creation(self):
        """Test de creación de SyncLog"""
        log = SyncLog(
            user_id="user-123",
            record_id="record-456",
            record_type="gasto",
            action="create",
            success=True
        )
        
        self.assertTrue(log.success)
        self.assertIsNone(log.error_message)
        self.assertIsInstance(log.id, str)


class TestCoreEntities(unittest.TestCase):
    """Tests para entidades del core"""
    
    def test_gasto_creation(self):
        """Test de creación de Gasto"""
        gasto = Gasto(
            nombre="Supermercado",
            monto=150.50,
            recurrente=True,
            categoria="alimentación"
        )
        
        self.assertEqual(gasto.nombre, "Supermercado")
        self.assertEqual(gasto.monto, 150.50)
        self.assertTrue(gasto.recurrente)
        self.assertEqual(gasto.categoria, "alimentación")
    
    def test_gasto_to_dict(self):
        """Test de conversión a diccionario"""
        gasto = Gasto(
            nombre="Test",
            monto=100.0,
            recurrente=False
        )
        
        data = gasto.to_dict()
        
        self.assertIn('id', data)
        self.assertEqual(data['nombre'], "Test")
        self.assertEqual(data['monto'], 100.0)
        self.assertFalse(data['recurrente'])
    
    def test_gasto_from_dict(self):
        """Test de creación desde diccionario"""
        data = {
            'id': 'custom-id',
            'nombre': 'Desde Dict',
            'monto': 200.0,
            'recurrente': True,
            'fecha': '2024-01-01',
            'categoria': 'test'
        }
        
        gasto = Gasto.from_dict(data)
        
        self.assertEqual(gasto.id, 'custom-id')
        self.assertEqual(gasto.nombre, 'Desde Dict')
        self.assertEqual(gasto.monto, 200.0)
    
    def test_ingreso_creation(self):
        """Test de creación de Ingreso"""
        ingreso = Ingreso(
            concepto="Salario",
            monto=1000.0,
            categoria="trabajo"
        )
        
        self.assertEqual(ingreso.concepto, "Salario")
        self.assertEqual(ingreso.monto, 1000.0)
    
    def test_presupuesto_creation(self):
        """Test de creación de Presupuesto"""
        presupuesto = Presupuesto(
            mes=1,
            anio=2024,
            categorias={'alimentación': 500, 'transporte': 200},
            total_presupuestado=700.0
        )
        
        self.assertEqual(presupuesto.mes, 1)
        self.assertEqual(presupuesto.anio, 2024)
        self.assertEqual(presupuesto.categorias['alimentación'], 500)


class TestFirebaseClientMock(unittest.TestCase):
    """Tests para FirebaseClient con mocks"""
    
    @patch('src.cloud.firebase_client.EnvConfig')
    @patch('src.cloud.firebase_client.os.path.exists')
    def test_firebase_disabled_by_default(self, mock_exists, mock_env):
        """Test que Firebase está deshabilitado por defecto"""
        mock_env.get.return_value = False
        mock_exists.return_value = False
        
        client = FirebaseClient()
        
        self.assertFalse(client.enabled)
    
    def test_generate_device_id(self):
        """Test de generación de device ID"""
        client = FirebaseClient()
        
        device_id = client.generate_device_id()
        
        self.assertIsInstance(device_id, str)
        self.assertGreater(len(device_id), 0)
    
    def test_singleton_pattern(self):
        """Test que FirebaseClient sigue patrón singleton"""
        client1 = FirebaseClient()
        client2 = FirebaseClient()
        
        self.assertIs(client1, client2)


class TestSyncEngineMock(unittest.TestCase):
    """Tests para SyncEngine con mocks"""
    
    @patch('src.cloud.sync_engine.FirebaseClient')
    def test_sync_engine_singleton(self, mock_firebase):
        """Test que SyncEngine sigue patrón singleton"""
        mock_firebase.return_value.enabled = False
        
        engine1 = SyncEngine()
        engine2 = SyncEngine()
        
        self.assertIs(engine1, engine2)
    
    @patch('src.cloud.sync_engine.FirebaseClient')
    def test_sync_disabled_when_not_authenticated(self, mock_firebase):
        """Test que sync se omite si no hay autenticación"""
        mock_firebase.return_value.enabled = True
        mock_firebase.return_value.is_authenticated.return_value = False
        
        engine = SyncEngine()
        result = engine.sync_all()
        
        self.assertEqual(result, {})


class TestDataMigration(unittest.TestCase):
    """Tests para migración de datos"""
    
    def test_gasto_serialization_roundtrip(self):
        """Test de serialización/deserialización de Gasto"""
        original = Gasto(
            nombre="Test Roundtrip",
            monto=99.99,
            recurrente=True,
            categoria="test"
        )
        
        data = original.to_dict()
        recovered = Gasto.from_dict(data)
        
        self.assertEqual(original.nombre, recovered.nombre)
        self.assertEqual(original.monto, recovered.monto)
        self.assertEqual(original.recurrente, recovered.recurrente)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
