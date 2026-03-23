"""
Módulo utilitario para manejar rutas de la aplicación
Proporciona rutas adecuadas para desktop y Android
"""

import os
import sys
from pathlib import Path


def app_data_dir() -> Path:
    """
    Obtiene el directorio de datos de la aplicación.

    En Android: usa user_data_dir de Kivy (ruta escribible)
    En Desktop: usa el directorio 'data' del proyecto

    Returns:
        Path: Ruta al directorio de datos
    """
    # Detectar Android explícitamente
    if sys.platform == "android":
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app is not None and hasattr(app, 'user_data_dir'):
                data_dir = Path(app.user_data_dir)
                # Asegurar que el directorio existe
                data_dir.mkdir(parents=True, exist_ok=True)
                return data_dir
        except Exception as e:
            # Logear error pero continuar con fallback
            print(f"WARNING: Error obteniendo user_data_dir en Android: {e}")

    # Fallback para desktop o si falla detección Android
    base_path = Path(__file__).resolve().parents[2]
    data_dir = base_path / "data"
    
    # Intentar crear el directorio si no existe
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # Si no hay permisos, usar temp directory
        import tempfile
        data_dir = Path(tempfile.gettempdir()) / "organizador_finanzas"
        data_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir


def db_file() -> Path:
    """Obtiene la ruta al archivo de base de datos"""
    return app_data_dir() / "finanzas.db"


def backup_file() -> Path:
    """Obtiene la ruta al archivo de backup"""
    return app_data_dir() / "finanzas_historial_backup.json"


def db_dir() -> Path:
    """Obtiene el directorio de la base de datos"""
    return app_data_dir()
