# src/core/initialization.py
"""
Sistema de inicialización automática de la aplicación.
Ejecuta validaciones y migraciones en el startup.
"""

from pathlib import Path
from typing import Tuple, Optional
from src.utils.logger import get_logger
from src.utils.db_migration import run_migrations, validate_database, backup_database
from src.utils.cache import get_cache
from src.utils.events import get_event_bus, AppEvents, Event
from src.config.env_config import BACKUP_ENABLED, LOG_LEVEL, DEBUG

logger = get_logger(__name__)


class AppInitializer:
    """Inicializador automático de la aplicación"""
    
    @staticmethod
    def validate_directories() -> bool:
        """Valida que existan todos los directorios necesarios"""
        logger.info("🔍 Validando directorios...")
        
        dirs_needed = ['data', 'data/backups', 'logs', 'assets']
        
        for dir_path in dirs_needed:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.debug(f"✅ Directorio ok: {dir_path}")
            except Exception as e:
                logger.error(f"❌ Error creando directorio {dir_path}: {e}")
                return False
        
        return True
    
    @staticmethod
    def initialize_database() -> bool:
        """Inicializa la base de datos con migraciones automáticas"""
        logger.info("🔄 Inicializando base de datos...")
        
        # Ejecutar migraciones
        if not run_migrations():
            logger.error("❌ Error en migraciones de base de datos")
            return False
        
        # Validar base de datos
        if not validate_database():
            logger.error("❌ Base de datos corrupta")
            if BACKUP_ENABLED:
                logger.info("📦 Creando backup de seguridad...")
                backup_database()
            return False
        
        logger.info("✅ Base de datos lista")
        return True
    
    @staticmethod
    def initialize_cache() -> bool:
        """Inicializa el sistema de caché"""
        logger.info("💾 Inicializando caché...")
        try:
            cache = get_cache()
            logger.info(f"✅ Caché inicializado (máx {cache.max_size} elementos)")
            return True
        except Exception as e:
            logger.error(f"❌ Error inicializando caché: {e}")
            return False
    
    @staticmethod
    def initialize_events() -> bool:
        """Inicializa el bus de eventos"""
        logger.info("📡 Inicializando bus de eventos...")
        try:
            bus = get_event_bus()
            logger.info("✅ Bus de eventos listo")
            return True
        except Exception as e:
            logger.error(f"❌ Error inicializando eventos: {e}")
            return False
    
    @staticmethod
    def initialize_logging() -> bool:
        """Inicializa el sistema de logging"""
        logger.info(f"📝 Logging configurado - Nivel: {LOG_LEVEL}")
        logger.debug(f"Debug mode: {DEBUG}")
        return True
    
    @staticmethod
    def run_all_checks() -> Tuple[bool, str]:
        """Ejecuta todas las verificaciones de inicialización"""
        logger.info("=" * 60)
        logger.info("🚀 INICIALIZANDO APLICACIÓN")
        logger.info("=" * 60)
        
        checks = [
            ("Logging", AppInitializer.initialize_logging),
            ("Directorios", AppInitializer.validate_directories),
            ("Base de datos", AppInitializer.initialize_database),
            ("Caché", AppInitializer.initialize_cache),
            ("Eventos", AppInitializer.initialize_events),
        ]
        
        failed_checks = []
        
        for check_name, check_func in checks:
            try:
                if not check_func():
                    failed_checks.append(check_name)
                    logger.error(f"❌ Falló: {check_name}")
            except Exception as e:
                failed_checks.append(check_name)
                logger.error(f"❌ Excepción en {check_name}: {e}")
        
        logger.info("=" * 60)
        
        if failed_checks:
            msg = f"Fallos en inicialización: {', '.join(failed_checks)}"
            logger.error(f"❌ {msg}")
            return False, msg
        
        logger.info("✅ APLICACIÓN INICIALIZADA CORRECTAMENTE")
        logger.info("=" * 60)
        
        # Publicar evento de inicialización completada
        bus = get_event_bus()
        bus.publish(Event(AppEvents.SUCCESS, {'message': 'App initialized'}))
        
        return True, "OK"


def initialize_app() -> bool:
    """Función de conveniencia para inicializar la app"""
    success, message = AppInitializer.run_all_checks()
    return success
