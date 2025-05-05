import PyInstaller.__main__
import os

# Obtener la ruta absoluta del directorio de ejecución actual
script_dir = os.path.dirname(os.path.abspath(__file__))

# Definir todos los archivos y carpetas que deben incluirse
additional_files = [
    os.path.join(script_dir, 'assets'),  # Carpeta de assets si la tienes
    # Agrega aquí otras carpetas o archivos
]

# Configuración para PyInstaller
PyInstaller.__main__.run([
    'main_app.py',                          # Tu script principal
    '--name=OrganizadorDeGastos',       # Nombre del ejecutable
    '--onefile',                        # Un solo archivo ejecutable
    '--windowed',                       # Sin ventana de consola
    '--add-data=assets;assets',         # Incluir carpetas adicionales
    '--hidden-import=babel.numbers',    # Para tkcalendar
    '--hidden-import=tkcalendar',
    '--additional-hooks-dir=hooks',
    '--clean',                          # Limpiar caché
    '--noconfirm',                      # No confirmar sobreescritura
    '--log-level=INFO',                 # Nivel de log
    '--uac-admin'                       # Pedir elevación de privilegios
])