# src/utils/decorators.py
"""
Decoradores útiles para la aplicación.
"""

import functools
import time
from typing import Callable, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


def timer(func: Callable) -> Callable:
    """Decorador para medir tiempo de ejecución"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.debug(f"{func.__name__} tomó {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"{func.__name__} falló después de {elapsed:.3f}s: {e}")
            raise
    
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorador para reintentar en caso de error"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Intento {attempt + 1}/{max_attempts} falló: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"Todos los {max_attempts} intentos fallaron")
            
            raise last_error
        
        return wrapper
    
    return decorator


def validate_types(**expected_types):
    """Decorador para validar tipos de argumentos"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Validar argumentos nombrados
            for key, value in kwargs.items():
                if key in expected_types:
                    if not isinstance(value, expected_types[key]):
                        raise TypeError(
                            f"Argumento '{key}' debe ser {expected_types[key].__name__}, "
                            f"no {type(value).__name__}"
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def safe_execute(default_return: Any = None):
    """Decorador para ejecutar funciones de forma segura con valor por defecto"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {e}", exc_info=True)
                return default_return
        
        return wrapper
    
    return decorator
