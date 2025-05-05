import os
import sys
import traceback
from model.data_manager import inicializar_db

def inicializar_db_wrapper():
    """
    Función wrapper para inicializar la base de datos.
    Proporciona manejo de errores adicional.
    
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """
    try:
        # Verificar que el directorio model existe
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_dir = os.path.join(base_dir, 'model')
        
        if not os.path.exists(model_dir):
            os.makedirs(model_dir, exist_ok=True)
            print(f"Directorio creado: {model_dir}")
            
        # Inicializar la base de datos
        inicializar_db()
        return True
    except Exception as e:
        error_msg = f"Error al inicializar la base de datos: {e}\n{traceback.format_exc()}"
        print(error_msg)
        
        # Escribir el error en un archivo de log
        try:
            with open('error_log.txt', 'a') as f:
                f.write(f"{error_msg}\n\n")
        except:
            pass
            
        return False

def backup_database():
    """
    Realiza una copia de seguridad de la base de datos.
    
    Returns:
        bool: True si el backup fue exitoso, False en caso contrario
    """
    try:
        import shutil
        from datetime import datetime
        
        # Ruta de la base de datos
        db_file = 'finanzas.db'
        
        # Verificar que el archivo existe
        if not os.path.exists(db_file):
            print(f"No se encontró la base de datos: {db_file}")
            return False
            
        # Crear nombre de archivo para el backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f'finanzas_backup_{timestamp}.db'
        
        # Crear directorio de backups si no existe
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
            
        backup_path = os.path.join(backup_dir, backup_file)
        
        # Copiar el archivo
        shutil.copy2(db_file, backup_path)
        print(f"Base de datos respaldada en: {backup_path}")
        return True
    except Exception as e:
        print(f"Error al crear backup: {e}")
        return False