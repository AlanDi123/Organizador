"""
Módulo utilitario para manejar rutas de la aplicación
Proporciona rutas adecuadas para desktop y Android
"""

from pathlib import Path


def app_data_dir() -> Path:
    """
    Obtiene el directorio de datos de la aplicación.
    
    En Android: usa user_data_dir de Kivy (ruta escribible)
    En Desktop: usa el directorio 'data' del proyecto
    
    Returns:
        Path: Ruta al directorio de datos
    """
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is not None:
            return Path(app.user_data_dir)
    except Exception:
        pass
    
    # Fallback para desktop
    return Path(__file__).resolve().parents[2] / "data"


def db_file() -> Path:
    """Obtiene la ruta al archivo de base de datos"""
    return app_data_dir() / "finanzas.db"


def backup_file() -> Path:
    """Obtiene la ruta al archivo de backup"""
    return app_data_dir() / "finanzas_historial_backup.json"


def db_dir() -> Path:
    """Obtiene el directorio de la base de datos"""
    return app_data_dir()
