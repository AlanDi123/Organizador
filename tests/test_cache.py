# tests/test_cache.py
"""
Tests para el sistema de caché.
"""

import pytest
import time
from src.utils.cache import Cache, cacheable, get_cache


class TestCache:
    """Tests para Cache"""
    
    def test_set_and_get(self):
        """Prueba guardar y obtener del caché"""
        cache = Cache(max_size=10, ttl=60)
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'
    
    def test_missing_key(self):
        """Prueba obtener clave inexistente"""
        cache = Cache()
        assert cache.get('nonexistent') is None
    
    def test_ttl_expiration(self):
        """Prueba expiración de TTL"""
        cache = Cache(ttl=1)
        cache.set('key', 'value')
        assert cache.get('key') == 'value'
        
        time.sleep(1.1)
        assert cache.get('key') is None
    
    def test_max_size(self):
        """Prueba límite de tamaño"""
        cache = Cache(max_size=3, ttl=60)
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        cache.set('key4', 'value4')  # Debe eliminar una
        
        assert cache.size() == 3
    
    def test_clear(self):
        """Prueba limpiar caché"""
        cache = Cache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.clear()
        assert cache.size() == 0


class TestCacheableDecorator:
    """Tests para decorador @cacheable"""
    
    def test_cacheable_function(self):
        """Prueba función cacheada"""
        call_count = [0]
        
        @cacheable(ttl=60)
        def expensive_function(x):
            call_count[0] += 1
            return x * 2
        
        # Primera llamada - debe ejecutar
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count[0] == 1
        
        # Segunda llamada - debe venir del caché
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count[0] == 1  # No debe incrementar


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
