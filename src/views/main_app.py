import tkinter as tk
from tkinter import messagebox
import os
import sys
import atexit
import gc
import logging
import traceback

# Definir directorios base (Vital para Linux)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger('main_app')

# Importaciones del proyecto
try:
    # Ajustamos el path por si acaso
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    from src.utils.utils import inicializar_db_wrapper, cerrar_conexiones_db, ThreadManager
    from src.controllers.app_controller import AppController
except ImportError as e:
    logger.error(f"Error crítico importando módulos internos: {e}")
    print(f"❌ Error crítico importando módulos: {e}")
    # No usamos input() para no bloquear
    sys.exit(1)

atexit.register(cerrar_conexiones_db)

def limpiar_recursos():
    """Libera recursos al cerrar"""
    try:
        if 'ThreadManager' in globals():
            ThreadManager.cleanup_threads()
        gc.collect()
        cerrar_conexiones_db()
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except:
            pass
        logger.info("Recursos liberados")
    except Exception as e:
        logger.error(f"Error al limpiar: {e}")

def main():
    print("🚀 Iniciando aplicación optimizada para sistemas con pocos recursos...")
    
    try:
        atexit.register(limpiar_recursos)
        
        # 1. Inicializar Base de Datos
        print("📊 Inicializando base de datos...")
        inicializar_db_wrapper()
        
        # 2. Crear Ventana Principal
        # Usar Tkinter estándar (muy ligero, compatible con todo)
        print("🎨 Usando Tkinter estándar (optimizado para bajo consumo)")
        root = tk.Tk()
        
        root.title("Organizador de Gastos e Ingresos")
        root.geometry('1200x800')
        
        # 3. Configurar Icono (Robusto para Linux)
        icon_name = "icon.png" # Preferible png en Linux
        icon_path = os.path.join(ASSETS_DIR, icon_name)
        
        if os.path.exists(icon_path):
            try:
                img = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, img)
            except Exception as e:
                print(f"⚠️ No se pudo cargar icono: {e}")
        
        # 4. Inicializar Controlador
        # IMPORTANTE: NO ocultamos la ventana (withdraw) para poder ver errores
        print("🧠 Cargando AppController...")
        
        # Pasamos root al controlador
        app = AppController(root)
        
        # 5. Protocolo de cierre
        def on_closing():
            if messagebox.askokcancel("Salir", "¿Estás seguro que deseas salir?"):
                limpiar_recursos()
                root.destroy()
                sys.exit(0)
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("✅ Todo listo. Iniciando bucle principal.")
        root.mainloop()
        
    except Exception as e:
        error_msg = f"❌ Error Fatal en ejecución: {e}"
        print(error_msg)
        traceback.print_exc()
        logger.error(error_msg)
        
        # Intentar mostrar error gráfico si la ventana existe
        try:
            messagebox.showerror("Error Fatal", f"Ocurrió un error:\n{e}")
        except:
            pass

if __name__ == "__main__":
    main()