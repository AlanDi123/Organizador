"""
Android Crash Diagnostic Script
Ejecutar con: adb logcat | grep -E "Python|Organizador"
"""

import sys
import traceback

def diagnose_android_crash():
    """Diagnóstico completo para crash de Android"""
    
    print("=" * 60)
    print("DIAGNÓSTICO ANDROID - Organizador App")
    print("=" * 60)
    
    # 1. Verificar plataforma
    print(f"\n1. Plataforma: {sys.platform}")
    print(f"   Es Android: {sys.platform == 'android'}")
    
    # 2. Verificar imports críticos
    print("\n2. Verificando imports críticos...")
    
    critical_imports = [
        ('kivy', 'Kivy framework'),
        ('kivymd', 'KivyMD UI'),
        ('requests', 'HTTP client'),
        ('sqlite3', 'Base de datos'),
    ]
    
    for module, desc in critical_imports:
        try:
            __import__(module)
            print(f"   ✓ {desc} ({module}) - OK")
        except ImportError as e:
            print(f"   ✗ {desc} ({module}) - FALLÓ: {e}")
    
    # 3. Verificar módulos PROHIBIDOS en Android
    print("\n3. Verificando módulos NO compatibles con Android...")
    
    forbidden_imports = [
        ('tkinter', 'Desktop UI'),
        ('firebase_admin', 'Server SDK'),
        ('google.cloud', 'Server SDK'),
    ]
    
    for module, desc in forbidden_imports:
        try:
            __import__(module)
            print(f"   ⚠ {desc} ({module}) - IMPORTADO (puede causar crash)")
        except ImportError:
            print(f"   ✓ {desc} ({module}) - No presente (correcto)")
    
    # 4. Verificar permisos Android
    print("\n4. Verificando permisos Android...")
    if sys.platform == 'android':
        try:
            from android.permissions import check_permission, Permission
            permissions = {
                'INTERNET': Permission.INTERNET,
                'ACCESS_NETWORK_STATE': Permission.ACCESS_NETWORK_STATE,
                'WRITE_EXTERNAL_STORAGE': Permission.WRITE_EXTERNAL_STORAGE,
                'READ_EXTERNAL_STORAGE': Permission.READ_EXTERNAL_STORAGE,
            }
            
            for name, perm in permissions.items():
                status = "CONCEDIDO" if check_permission(perm) else "DENEGADO"
                print(f"   {name}: {status}")
        except Exception as e:
            print(f"   Error al verificar permisos: {e}")
    else:
        print("   (Solo disponible en Android)")
    
    # 5. Verificar rutas de base de datos
    print("\n5. Verificando rutas de base de datos...")
    try:
        from src.utils.paths import app_data_dir, db_file, backup_file
        print(f"   Directorio app: {app_data_dir()}")
        print(f"   DB file: {db_file()}")
        print(f"   Backup: {backup_file()}")
        
        # Verificar si se puede escribir
        import os
        db_dir = app_data_dir()
        os.makedirs(db_dir, exist_ok=True)
        print(f"   ✓ Escritura en DB dir: OK")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        traceback.print_exc()
    
    # 6. Verificar Firebase REST
    print("\n6. Verificando Firebase REST client...")
    try:
        from src.cloud.firebase_client import FirebaseClient
        client = FirebaseClient()
        print(f"   Habilitado: {client.enabled}")
        print(f"   API Key presente: {bool(client.api_key)}")
        print(f"   Project ID: {client.project_id}")
        print(f"   ✓ FirebaseClient inicializa sin crash")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        traceback.print_exc()
    
    # 7. Verificar Sync Engine
    print("\n7. Verificando Sync Engine...")
    try:
        from src.cloud.sync_engine import SyncEngine
        engine = SyncEngine()
        print(f"   ✓ SyncEngine inicializa sin crash")
        print(f"   Firebase enabled: {engine.firebase.enabled}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        traceback.print_exc()
    
    # 8. Verificar Data Manager
    print("\n8. Verificando Data Manager...")
    try:
        from src.models.data_manager import DBConnectionManager
        conn = DBConnectionManager.get_instance()
        print(f"   ✓ DBConnectionManager inicializa sin crash")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("FIN DEL DIAGNÓSTICO")
    print("=" * 60)


if __name__ == '__main__':
    diagnose_android_crash()
