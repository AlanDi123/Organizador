# src/utils/cache.py
"""
Sistema de caché para mejorar la performance de la aplicación.
"""

import time
from typing import Any, Dict, Optional, Callable
from functools import wraps


class Cache:
    """Sistema de caché simple con expiración"""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, tuple] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché"""
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        
        # Verificar expiración
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Guarda un valor en el caché"""
        # Limpiar si se alcanzó el límite
        if len(self.cache) >= self.max_size:
            # Eliminar el más antiguo
            oldest_key = min(self.cache.keys(), 
                            key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Limpia todo el caché"""
        self.cache.clear()
    
    def delete(self, key: str) -> None:
        """Elimina una clave específica"""
        self.cache.pop(key, None)
    
    def size(self) -> int:
        """Retorna el tamaño actual del caché"""
        return len(self.cache)


# Instancia global del caché
_global_cache = Cache()


def cacheable(ttl: int = 3600):
    """Decorador para cachear resultados de funciones"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Crear clave del caché
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Intentar obtener del caché
            cached = _global_cache.get(key)
            if cached is not None:
                return cached
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            _global_cache.set(key, result)
            
            return result
        
        return wrapper
    
    return decorator


def get_cache() -> Cache:
    """Obtiene la instancia global del caché"""
    return _global_cache
