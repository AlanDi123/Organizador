import tkinter as tk
from tkinter import messagebox
import os
import sys
import subprocess
import traceback
import atexit
import gc
import logging

from utils import ThreadManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger('main_app')

# Configurar opciones para Windows
def configurar_para_windows():
    """Configura ajustes específicos para Windows si está disponible"""
    if hasattr(sys, 'getwindowsversion'):
        try:
            import ctypes
            from ctypes import windll
            
            # Ajustar configuración DPI para evitar problemas de escalado
            windll.shcore.SetProcessDpiAwareness(1)
            logger.info("Configuración Windows aplicada")
            return True
        except Exception as e:
            logger.error(f"No se pudo configurar para Windows: {e}")
    return False

# Importaciones envueltas en try-except para manejar errores de importación
try:
    from utils import inicializar_db_wrapper, cerrar_conexiones_db
    from app_controller import AppController
except ImportError as e:
    logger.error(f"Error al importar módulos: {e}")
    input("Presione Enter para salir...")
    sys.exit(1)

# Registro de función para cierre de recursos
atexit.register(cerrar_conexiones_db)

# Verificar dependencias
def verificar_dependencias():
    """
    Verifica e intenta instalar las dependencias necesarias.
    
    Returns:
        bool: True si todas las dependencias están disponibles, False en caso contrario
    """
    dependencias_requeridas = ['pillow', 'requests', 'matplotlib', 'tkcalendar', 'numpy']
    dependencias_faltantes = []
    
    try:
        # Intentamos importar todas las dependencias necesarias
        import tkinter
        
        try:
            from PIL import Image, ImageTk
        except ImportError:
            dependencias_faltantes.append('pillow')
        
        try:
            import requests
        except ImportError:
            dependencias_faltantes.append('requests')
        
        try:
            import matplotlib
        except ImportError:
            dependencias_faltantes.append('matplotlib')
            
        try:
            import numpy
        except ImportError:
            dependencias_faltantes.append('numpy')
            
        try:
            from tkcalendar import DateEntry
        except ImportError:
            dependencias_faltantes.append('tkcalendar')
        
        if not dependencias_faltantes:
            logger.info("Dependencias verificadas correctamente.")
            return True
            
        logger.warning(f"Dependencias faltantes: {', '.join(dependencias_faltantes)}")
        print(f"Dependencias faltantes: {', '.join(dependencias_faltantes)}")
        print("Intentando instalar...")
        
        try:
            for dep in dependencias_faltantes:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            logger.info("Dependencias instaladas correctamente.")
            return True
        except Exception as e:
            logger.error(f"Error al instalar dependencias: {e}")
            print(f"Error al instalar dependencias: {e}")
            print(f"Por favor, instale manualmente {', '.join(dependencias_faltantes)} usando pip.")
            
            # Esperar input del usuario antes de continuar
            input("Presione Enter para continuar de todos modos...")
            return False
            
    except Exception as e:
        logger.error(f"Error durante la verificación de dependencias: {e}")
        print(f"Error durante la verificación de dependencias: {e}")
        print(traceback.format_exc())
        input("Presione Enter para continuar de todos modos...")
        return False

# Función para liberar recursos al cerrar
def limpiar_recursos():
    """Libera recursos de memoria al cerrar la aplicación"""
    try:
        # Limpiar hilos activos
        if 'ThreadManager' in globals():
            ThreadManager.cleanup_threads()
            ThreadManager.join_all(timeout=0.5)
        
        # Forzar liberación de memoria
        gc.collect()
        
        # Cerrar conexiones de bases de datos
        cerrar_conexiones_db()
        
        # Cerrar figuras de matplotlib
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except:
            pass
        
        logger.info("Recursos liberados correctamente")
    except Exception as e:
        logger.error(f"Error al liberar recursos: {e}")

# Función principal
def main():
    """
    Función principal que inicializa y ejecuta la aplicación.
    """
    try:
        # Registrar función de limpieza al salir
        atexit.register(limpiar_recursos)
        
        # Configurar para Windows si es posible
        configurar_para_windows()
        
        # Verificar dependencias solo si no se está ejecutando desde un .bat
        if not os.environ.get('RUNNING_FROM_BAT'):
            verificar_dependencias()
            os.environ['RUNNING_FROM_BAT'] = '1'
        
        # Inicializa la base de datos
        inicializar_db_wrapper()
        
        # Crear la ventana principal
        root = tk.Tk()
        root.title("Organizador de Gastos e Ingresos")
        
        # Configurar ventana
        try:
            root.state('zoomed')  # Maximizar la ventana en Windows
        except tk.TclError:
            # En sistemas que no soporten 'zoomed', usar geometry
            root.geometry('1200x800')
        
        # Configurar icono de la aplicación si existe
        icon_paths = [
            os.path.join("assets", "icon.ico"), 
            "icon.ico", 
            os.path.join("assets", "icon.png"), 
            "icon.png"
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    if icon_path.endswith('.ico'):
                        root.iconbitmap(icon_path)
                    elif icon_path.endswith('.png'):
                        # Para sistemas que no soportan .ico
                        logo = tk.PhotoImage(file=icon_path)
                        root.iconphoto(True, logo)
                    break
                except tk.TclError:
                    pass
        
        # Configurar estilo para maximizar ventanas
        try:
            if hasattr(sys, 'getwindowsversion'):
                # Personalizar estilo de ventana principal
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)  # GWL_STYLE
                style |= 0x00010000  # WS_MAXIMIZEBOX
                ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)
        except Exception as e:
            logger.warning(f"Aviso: No se pudo configurar el estilo de maximizar: {e}")
        
        # Deshabilitar temporalmente la ventana durante la inicialización
        root.withdraw()
            
        # Inicializar el controlador de la aplicación
        app = AppController(root)
        
        # Configurar manejo de cierre
        def on_closing():
            if messagebox.askokcancel("Salir", "¿Estás seguro que deseas salir?"):
                # Limpieza antes de cerrar
                limpiar_recursos()
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Mostrar la ventana ya configurada
        root.deiconify()
        
        # Forzar actualización inicial completa
        root.update_idletasks()
        
        # Iniciar la aplicación
        root.mainloop()
        
        # Limpieza final
        limpiar_recursos()
        
    # Continuación de main_app.py
        
    except Exception as e:
        error_msg = f"Error durante la ejecución: {e}\n\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        try:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
        except:
            # Si no se puede mostrar una ventana de mensaje, usar console
            print("No se pudo mostrar ventana de error.")
            
        input("Presione Enter para salir...")
        
# Punto de entrada principal
if __name__ == "__main__":
    main()