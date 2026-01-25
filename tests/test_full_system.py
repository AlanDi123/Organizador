#!/usr/bin/env python
# tests/test_full_system.py
"""
Test de sistema completo - Verifica que todos los módulos funcionan
"""

import os
import sys
import tempfile
import sqlite3

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_migration():
    """Prueba las migraciones de base de datos"""
    try:
        # Crear una BD temporal
        temp_db = tempfile.mktemp(suffix='.db')
        
        # Parchear la ruta de BD para usar la temporal
        import src.utils.db_migration as db_mod
        original_db = db_mod.DB_FILE
        db_mod.DB_FILE = temp_db
        
        # Ejecutar migraciones
        from src.utils.db_migration import run_migrations, get_db_version
        
        success = run_migrations()
        assert success == True, "run_migrations() falló"
        
        # Verificar versión
        version = get_db_version()
        assert version == 2, f"Versión incorrecta: {version} (esperado 2)"
        
        # Verificar estructura de tablas
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['gastos', 'ingresos', 'categorias', 'presupuesto', 'version']
        for table in required_tables:
            assert table in tables, f"Tabla {table} no existe"
        
        conn.close()
        
        # Limpiar
        os.remove(temp_db)
        if os.path.exists(temp_db + '-journal'):
            os.remove(temp_db + '-journal')
        db_mod.DB_FILE = original_db
        
        print("✅ Database migration funcionando correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en Database migration: {e}")
        import traceback
        traceback.print_exc()
        # Restaurar ruta original
        import src.utils.db_migration as db_mod
        db_mod.DB_FILE = original_db
        return False

def test_cache():
    """Prueba el sistema de cache"""
    try:
        from src.utils.cache import Cache, get_cache
        
        cache = Cache(max_size=100, ttl=3600)
        
        # Test set/get
        cache.set('test_key', 'test_value')
        value = cache.get('test_key')
        assert value == 'test_value', "Cache get/set falló"
        
        # Test non-existent key
        assert cache.get('non_existent') is None, "Cache devolvió valor para clave inexistente"
        
        # Test global cache
        global_cache = get_cache()
        global_cache.set('global_test', 'global_value')
        assert global_cache.get('global_test') == 'global_value'
        
        print("✅ Cache funcionando correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en Cache: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logger():
    """Prueba el sistema de logging"""
    try:
        from src.utils.logger import get_logger
        
        logger = get_logger('test_module')
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        print("✅ Logger funcionando correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en Logger: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_decorators():
    """Prueba los decoradores"""
    try:
        from src.utils.decorators import timer, safe_execute, validate_types, retry
        
        @timer
        def slow_function():
            total = 0
            for i in range(1000):
                total += i
            return total
        
        result = slow_function()
        assert result == 499500, "Función decorada con @timer devolvió resultado incorrecto"
        
        @safe_execute(default_return=0)
        def risky_function():
            return 1 / 0  # Esta falla deliberadamente
        
        # safe_execute no debe lanzar excepción y devuelve 0
        result = risky_function()
        assert result == 0, f"safe_execute debería devolver 0, devolvió {result}"
        
        # validate_types con parámetros
        @validate_types(x=int, y=int)
        def add_numbers(x, y):
            return x + y
        
        result = add_numbers(5, 3)
        assert result == 8, "add_numbers falló"
        
        print("✅ Decoradores funcionando correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en Decoradores: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Prueba que se pueden importar los módulos principales"""
    try:
        from src.utils.logger import get_logger
        from src.utils.cache import Cache, get_cache
        from src.utils.decorators import timer, retry, validate_types, safe_execute
        from src.utils.db_migration import run_migrations, get_db_version
        
        print("✅ Todas las importaciones exitosas")
        return True
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Ejecuta todos los tests del sistema"""
    print("\n" + "="*60)
    print("🧪 EJECUTANDO TESTS DEL SISTEMA COMPLETO")
    print("="*60 + "\n")
    
    tests = [
        ("Importaciones", test_imports),
        ("Logger", test_logger),
        ("Cache", test_cache),
        ("Decorators", test_decorators),
        ("Database Migration", test_database_migration),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Probando {name}...")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} - Error no manejado: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n📈 Total: {passed}/{total} tests pasados")
    print("="*60 + "\n")
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
