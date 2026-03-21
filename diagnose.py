#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la instalación
"""

import sys
import os
from pathlib import Path

print("=" * 60)
print("  DIAGNÓSTICO - Organizador de Gastos")
print("=" * 60)

# Versión de Python
print(f"\n✓ Python: {sys.version}")
print(f"  Ruta: {sys.executable}")

# Sistema operativo
print(f"\n✓ Sistema: {sys.platform}")
if sys.platform == 'linux':
    print(f"  Linux: {os.uname().release}")
elif sys.platform == 'win32':
    print(f"  Windows: {os.environ.get('OS', 'Unknown')}")

# Directorio actual
print(f"\n✓ Directorio: {os.getcwd()}")

# Verificar dependencias
print("\n" + "=" * 60)
print("  DEPENDENCIAS")
print("=" * 60)

dependencies = {
    'Desktop UI': ['tkinter', 'tkcalendar', 'PIL', 'matplotlib', 'requests'],
    'Mobile UI': ['kivy', 'kivymd'],
    'Cloud Sync': ['firebase_admin', 'google.cloud.firestore'],
    'Utils': ['pydantic', 'dotenv'],
    'Tests': ['pytest'],
}

missing = []

for category, modules in dependencies.items():
    print(f"\n{category}:")
    for module in modules:
        try:
            __import__(module)
            mod = sys.modules[module]
            version = getattr(mod, '__version__', 'N/A')
            print(f"  ✓ {module}: {version}")
        except ImportError:
            print(f"  ✗ {module}: NO INSTALADO")
            missing.append(module)

# Verificar archivos importantes
print("\n" + "=" * 60)
print("  ARCHIVOS IMPORTANTES")
print("=" * 60)

important_files = [
    'run.py',
    'main.py',
    'requirements.txt',
    'buildozer.spec',
    '.env',
    '.env.example',
    'README.md',
    'FIREBASE_SETUP.md',
    'QUICKSTART.md',
]

for filepath in important_files:
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"  ✓ {filepath} ({size} bytes)")
    else:
        print(f"  ✗ {filepath}: NO ENCONTRADO")

# Verificar estructura de directorios
print("\n" + "=" * 60)
print("  ESTRUCTURA DE DIRECTORIOS")
print("=" * 60)

directories = [
    'src/cloud',
    'src/core',
    'src/mobile',
    'src/views',
    'src/models',
    'src/utils',
    'tests',
    'assets',
    'data',
]

for directory in directories:
    if os.path.isdir(directory):
        files_count = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
        print(f"  ✓ {directory}/ ({files_count} archivos)")
    else:
        print(f"  ✗ {directory}/: NO ENCONTRADO")

# Verificar Firebase
print("\n" + "=" * 60)
print("  CONFIGURACIÓN FIREBASE")
print("=" * 60)

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    firebase_enabled = os.getenv('FIREBASE_ENABLED', 'False')
    firebase_creds = os.getenv('FIREBASE_CREDENTIALS_PATH', '')
    firebase_project = os.getenv('FIREBASE_PROJECT_ID', '')
    
    print(f"  FIREBASE_ENABLED: {firebase_enabled}")
    print(f"  FIREBASE_CREDENTIALS_PATH: {firebase_creds}")
    print(f"  FIREBASE_PROJECT_ID: {firebase_project}")
    
    if firebase_enabled.lower() == 'true':
        if os.path.exists(firebase_creds):
            print(f"  ✓ Credenciales encontradas")
        else:
            print(f"  ✗ Credenciales NO encontradas: {firebase_creds}")
    else:
        print(f"  ℹ Firebase deshabilitado (modo offline)")
        
except Exception as e:
    print(f"  ✗ Error al leer configuración: {e}")

# Resumen
print("\n" + "=" * 60)
print("  RESUMEN")
print("=" * 60)

if missing:
    print(f"\n⚠ Faltan {len(missing)} dependencias:")
    for dep in missing:
        print(f"  - {dep}")
    print(f"\nInstalar con: pip install {' '.join(missing)}")
else:
    print("\n✓ ¡Todas las dependencias están instaladas!")

# Verificar buildozer
if sys.platform == 'linux':
    print("\n" + "=" * 60)
    print("  BUILD ANDROID (Buildozer)")
    print("=" * 60)
    
    try:
        import buildozer
        print(f"  ✓ Buildozer: {buildozer.__version__}")
    except ImportError:
        print(f"  ✗ Buildozer: NO INSTALADO")
        print(f"    Instalar con: pip install buildozer")
    
    # Verificar Java
    try:
        import subprocess
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✓ Java: {result.stderr.split(chr(10))[0]}")
        else:
            print(f"  ✗ Java: NO ENCONTRADO")
    except FileNotFoundError:
        print(f"  ✗ Java: NO INSTALADO")

print("\n" + "=" * 60)
print("  DIAGNÓSTICO COMPLETADO")
print("=" * 60)

if missing:
    sys.exit(1)
else:
    print("\n✓ Todo está listo para ejecutar la app!")
    print("  Desktop: python run.py")
    print("  Móvil: ./build_apk.sh")
    sys.exit(0)
