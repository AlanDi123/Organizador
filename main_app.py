import tkinter as tk
from tkinter import messagebox
import os
import sys
import subprocess
import traceback

# Importaciones envueltas en try-except para manejar errores de importación
try:
    from utils import inicializar_db_wrapper
    from ui.app_controller import AppController
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    input("Presione Enter para salir...")
    sys.exit(1)

# Verificar dependencias
def verificar_dependencias():
    """
    Verifica e intenta instalar las dependencias necesarias.
    
    Returns:
        bool: True si todas las dependencias están disponibles, False en caso contrario
    """
    dependencias_requeridas = ['pillow', 'requests', 'tkcalendar']
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
            from tkcalendar import DateEntry
        except ImportError:
            dependencias_faltantes.append('tkcalendar')
        
        if not dependencias_faltantes:
            print("Dependencias verificadas correctamente.")
            return True
            
        print(f"Dependencias faltantes: {', '.join(dependencias_faltantes)}")
        print("Intentando instalar...")
        
        try:
            for dep in dependencias_faltantes:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print("Dependencias instaladas correctamente.")
            return True
        except Exception as e:
            print(f"Error al instalar dependencias: {e}")
            print(f"Por favor, instale manualmente {', '.join(dependencias_faltantes)} usando pip.")
            
            # Esperar input del usuario antes de continuar
            input("Presione Enter para continuar de todos modos...")
            return False
            
    except Exception as e:
        print(f"Error durante la verificación de dependencias: {e}")
        print(traceback.format_exc())
        input("Presione Enter para continuar de todos modos...")
        return False

# Función principal
def main():
    """
    Función principal que inicializa y ejecuta la aplicación.
    """
    try:
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
        icon_paths = ["assets/icon.ico", "icon.ico", "assets/icon.png", "icon.png"]
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                try:
                    root.iconbitmap(icon_path) if icon_path.endswith('.ico') else None
                    break
                except tk.TclError:
                    pass
        
        # Inicializar el controlador de la aplicación
        app = AppController(root)
        
        # Configurar manejo de cierre
        def on_closing():
            if messagebox.askokcancel("Salir", "¿Estás seguro que deseas salir?"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Iniciar la aplicación
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Error durante la ejecución: {e}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        try:
            messagebox.showerror("Error", f"Ocurrió un error: {e}")
        except:
            # Si no se puede mostrar una ventana de mensaje, usar console
            print("No se pudo mostrar ventana de error.")
            
        input("Presione Enter para salir...")

# Punto de entrada principal
if __name__ == "__main__":
    main()