import os
import subprocess
import shutil
import sys

# Comprobar que el icono existe
icon_path = "icono.ico"
if not os.path.exists(icon_path):
    print(f"ADVERTENCIA: No se encontró el archivo {icon_path} en el directorio actual.")
    print("El ejecutable se creará sin icono personalizado.")
    icon_option = []
else:
    print(f"Icono encontrado: {icon_path}")
    icon_option = [f"--icon={icon_path}"]

# Definir el nombre del ejecutable (sin espacios para evitar problemas)
output_name = "OrganizadorDeGastos"

# Asegurarse de que todas las dependencias estén instaladas
print("Verificando dependencias necesarias...")
dependencies = ["pyinstaller", "matplotlib", "pillow", "pywin32"]
for dep in dependencies:
    try:
        __import__(dep)
    except ImportError:
        print(f"Instalando {dep}...")
        subprocess.run([sys.executable, "-m", "pip", "install", dep])

# Resolver el problema de stdin
runtime_hook = "runtime_hook.py"
with open(runtime_hook, "w") as f:
    f.write("""
# Este hook soluciona problemas con stdin/stdout en aplicaciones GUI
import sys
import os

# Redirigir stdin/stdout/stderr
if hasattr(sys, 'frozen'):
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    sys.stdin = open(os.devnull, 'r')
""")

print("Iniciando compilación con PyInstaller...")
print(f"Usando Python: {sys.executable}")

# Ejecutar PyInstaller como módulo en la misma versión de Python
pyinstaller_cmd = [
    sys.executable,  # Usar la misma versión de Python que está ejecutando este script
    "-m",
    "PyInstaller",
    "--name", output_name,
    "--onefile",
    "--windowed",  # Sin consola
    "--clean",
    "--noconfirm",
]

# Añadir opción de icono si existe
if icon_option:
    pyinstaller_cmd.append(icon_option[0])

# Añadir datos y recursos
if os.path.exists("assets"):
    pyinstaller_cmd.append("--add-data")
    pyinstaller_cmd.append("assets;assets")

# Añadir todas las importaciones ocultas necesarias
hidden_imports = [
    "PIL", "PIL._tkinter_finder", "tkinter", "sqlite3", 
    "matplotlib", "matplotlib.backends.backend_tkagg",
    "numpy", "pandas", "locale", "calendar", "datetime",
    "requests", "io"  # Añadidos basados en tu código
]

for imp in hidden_imports:
    pyinstaller_cmd.append("--hidden-import=" + imp)

# Agregar runtime hook
pyinstaller_cmd.append("--runtime-hook")
pyinstaller_cmd.append(runtime_hook)

# Añadir el script principal
pyinstaller_cmd.append("main_app.py")

print("Ejecutando comando:", " ".join(pyinstaller_cmd))

# Ejecutar PyInstaller
result = subprocess.run(pyinstaller_cmd)

if result.returncode == 0:
    print("\n✅ Compilación completada con éxito.")
    
    # Copiar archivos adicionales necesarios al directorio dist
    print("\nCopiando archivos necesarios...")
    files_to_copy = ["finanzas.db"]
    for file in files_to_copy:
        if os.path.exists(file):
            print(f"Copiando {file} al directorio de distribución")
            shutil.copy2(file, os.path.join("dist", file))
    
    print(f"\n🎉 ¡Listo! Tu aplicación está disponible en: dist/{output_name}.exe")
    print("\nRecuerda distribuir el archivo .exe junto con cualquier")
    print("base de datos o archivo de recursos necesario.")
    
    # Limpiar archivo temporal
    if os.path.exists(runtime_hook):
        os.remove(runtime_hook)
else:
    print("\n❌ Error durante la compilación.")
    print(f"Código de error: {result.returncode}")
    print("Verifica que todas las dependencias estén instaladas correctamente.")
    print("Intenta ejecutar: pip install PyInstaller==6.3.0 matplotlib pillow")