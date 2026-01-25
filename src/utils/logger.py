# src/utils/logger.py
"""
Sistema de logging centralizado y robusto.
"""

import logging
import logging.handlers
from pathlib import Path
from src.config import AppConfig


class Logger:
    """Logger centralizado para toda la aplicación"""
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa el sistema de logging"""
        # Crear directorio de logs si no existe
        log_dir = Path(AppConfig.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar formato
        self.formatter = logging.Formatter(AppConfig.LOG_FORMAT)
        
        # Configurar nivel de logging
        self.level = getattr(logging, AppConfig.LOG_LEVEL.upper())
    
    def get_logger(self, name: str) -> logging.Logger:
        """Obtiene o crea un logger para un módulo"""
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.level)
        
        # Handler para archivo
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                AppConfig.LOG_FILE,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=5
            )
            file_handler.setFormatter(self.formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Error configurando file handler: {e}")
        
        # Handler para consola (solo en debug)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        console_handler.setLevel(logging.WARNING)
        logger.addHandler(console_handler)
        
        self._loggers[name] = logger
        return logger


def get_logger(module_name: str) -> logging.Logger:
    """Función helper para obtener loggers"""
    return Logger().get_logger(module_name)
