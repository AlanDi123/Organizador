#!/usr/bin/env python3
"""
Script para compilar Organizador a .exe standalone sin Python requerido
Usa auto-py-to-exe (wrapper de PyInstaller) para una compilación optimizada
"""

import subprocess
import sys
import os

def build_organizador():
    """Compila Organizador.exe con todas las dependencias incluidas"""
    
    print("=" * 60)
    print("🔨 COMPILANDO ORGANIZADOR A EJECUTABLE WINDOWS")
    print("=" * 60)
    print()
    
    # Configuración de PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",  # Un solo archivo
        "--windowed",  # Sin consola
        "--name", "Organizador",  # Nombre del ejecutable
        "--icon", "assets/icono.ico" if os.path.exists("assets/icono.ico") else None,
        "--add-data", "src:src",  # Incluir código fuente
        "--add-data", "assets:assets",  # Incluir assets
        "--add-data", "data:data",  # Incluir datos
        "--hidden-import", "tkinter",
        "--hidden-import", "tkcalendar",
        "--hidden-import", "requests",
        "--hidden-import", "matplotlib",
        "--hidden-import", "matplotlib.pyplot",
        "--clean",  # Limpiar builds anteriores
        "--noconfirm",  # No preguntar confirmaciones
        "run.py"
    ]
    
    # Remover None values
    cmd = [x for x in cmd if x is not None]
    
    print(f"Comando: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            print()
            print("=" * 60)
            print("✅ ¡COMPILACIÓN EXITOSA!")
            print("=" * 60)
            print()
            print("📦 Tu ejecutable está en:")
            print(f"   → dist/Organizador.exe")
            print()
            print("📋 Características del .exe:")
            print("   ✓ Funciona sin Python instalado")
            print("   ✓ Todas las dependencias incluidas")
            print("   ✓ Sin consola (interfaz limpia)")
            print()
            print("🚀 Para usar:")
            print("   1. Copia dist/Organizador.exe a donde quieras")
            print("   2. Haz doble clic para ejecutar")
            print("   3. ¡Listo! No necesita nada más")
            print()
    
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR EN LA COMPILACIÓN (Código: {e.returncode})")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    build_organizador()
