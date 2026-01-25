# src/config/env_config.py
"""
Configuración desde variables de entorno con validación automática.
"""

from pathlib import Path
from typing import Optional, Any, Dict
import os

# Cargar variables de entorno
def load_env(env_file: str = ".env") -> Dict[str, str]:
    """Carga archivo .env y retorna diccionario"""
    env_vars = {}
    env_path = Path(env_file)
    
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
    
    return env_vars


class EnvConfig:
    """Configuración basada en variables de entorno con valores por defecto"""
    
    _env_vars = load_env()
    
    @classmethod
    def get(cls, key: str, default: Any = None, required: bool = False) -> Any:
        """Obtiene valor de variable de entorno con validación"""
        value = cls._env_vars.get(key) or os.getenv(key)
        
        if value is None:
            if required:
                raise ValueError(f"Variable de entorno requerida '{key}' no configurada")
            return default
        
        return cls._parse_value(value)
    
    @staticmethod
    def _parse_value(value: str) -> Any:
        """Parsea el valor a su tipo apropiado"""
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
        elif value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Retorna todas las variables cargadas"""
        return cls._env_vars.copy()


# Valores de configuración accesibles
APP_NAME = EnvConfig.get('APP_NAME', 'Organizador de Gastos Inteligente')
APP_VERSION = EnvConfig.get('APP_VERSION', '2.0.0')
DEBUG = EnvConfig.get('DEBUG', False)

DB_PATH = EnvConfig.get('DB_PATH', 'data/finanzas.db')
BACKUP_ENABLED = EnvConfig.get('BACKUP_ENABLED', True)
AUTO_BACKUP_INTERVAL = EnvConfig.get('AUTO_BACKUP_INTERVAL', 3600)

LOG_LEVEL = EnvConfig.get('LOG_LEVEL', 'INFO')
LOG_FILE = EnvConfig.get('LOG_FILE', 'logs/app.log')

DEFAULT_THEME = EnvConfig.get('DEFAULT_THEME', 'light')
WINDOW_WIDTH = EnvConfig.get('WINDOW_WIDTH', 1000)
WINDOW_HEIGHT = EnvConfig.get('WINDOW_HEIGHT', 700)

ENABLE_AI = EnvConfig.get('ENABLE_AI', True)
ENABLE_DARK_MODE = EnvConfig.get('ENABLE_DARK_MODE', True)
ENABLE_EXPORT = EnvConfig.get('ENABLE_EXPORT', True)
ENABLE_IMPORT = EnvConfig.get('ENABLE_IMPORT', True)

CACHE_TTL = EnvConfig.get('CACHE_TTL', 3600)
MAX_CACHE_SIZE = EnvConfig.get('MAX_CACHE_SIZE', 100)
REFRESH_RATE = EnvConfig.get('REFRESH_RATE', 1000)

OPENAI_ENABLED = EnvConfig.get('OPENAI_ENABLED', False)
AI_MODEL = EnvConfig.get('AI_MODEL', 'gpt-3.5-turbo')
