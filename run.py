import sys
import os
import traceback

# --- 1. CONFIGURACIÓN DE RUTAS ---
# Obtenemos la carpeta donde estamos (la raíz del proyecto)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Agregamos la raíz a las rutas de búsqueda de Python
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print(f"📂 Directorio raíz configurado: {BASE_DIR}")

# --- 2. TRUCOS PARA LINUX ---
os.environ['RUNNING_FROM_BAT'] = '1'

if os.environ.get('XDG_SESSION_TYPE') == 'wayland':
    os.environ['GDK_BACKEND'] = 'x11'

print("🐧 Configuración de Linux aplicada.")

# --- 3. INICIALIZACIÓN AUTOMÁTICA ---
print("\n" + "="*60)
print("🔧 INICIALIZANDO SISTEMA...")
print("="*60 + "\n")

try:
    from src.core.initialization import initialize_app
    
    if not initialize_app():
        print("\n❌ Error durante la inicialización.")
        print("Intenta ejecutar nuevamente o verifica los logs.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ SISTEMA LISTO - INICIANDO UI...")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"\n❌ Error crítico en inicialización: {e}")
    traceback.print_exc()
    sys.exit(1)

# --- 4. EJECUCIÓN ---
try:
    print("🚀 Importando aplicación...")
    from src.views import main_app
    
    print("🎬 Ejecutando función main()...")
    # Llamamos a la función principal
    main_app.main()

except ImportError as e:
    print("\n❌ ERROR DE IMPORTACIÓN:")
    print(f"   {e}")
    print("   Asegúrate de haber ejecutado 'bash arreglar_todo.sh' previamente.")
except Exception as e:
    print("\n❌ ERROR DE EJECUCIÓN:")
    traceback.print_exc()
    print("\n💡 TIP: Revisa el archivo 'app.log' si se creó en esta carpeta.")

print("👋 Fin del lanzador.")