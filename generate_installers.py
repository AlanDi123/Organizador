#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  GENERADOR DE INSTALADORES - Organizador v1.0.0
  Genera instaladores compilados para Windows y Linux
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import zipfile
import tarfile
import subprocess
from datetime import datetime
from pathlib import Path

# Colores
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}╔════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║{RESET}  {text}")
    print(f"{BLUE}╚════════════════════════════════════════════════════╝{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_info(text):
    print(f"{YELLOW}➜{RESET} {text}")

def check_dist_exists():
    """Verifica que exista la carpeta compilada por PyInstaller"""
    if not os.path.isdir("dist/Organizador"):
        print_error("No se encontró 'dist/Organizador'")
        print_info("Primero debes compilar con: pyinstaller organizador.spec -y")
        return False
    print_success("Carpeta compilada encontrada: dist/Organizador")
    return True

def create_windows_installer():
    """Crea el instalador para Windows"""
    print_info("Generando instalador Windows...")
    
    dist_path = Path("dist/Organizador")
    if not dist_path.exists():
        print_error("No se encontró dist/Organizador para Windows")
        return False
    
    # Para Windows necesitarías NSIS compilado, aquí solo creamos el ZIP
    zip_path = f"instaladores_ready/Organizador-Windows-v1.0.0.zip"
    
    os.makedirs("instaladores_ready", exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(dist_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "dist")
                zf.write(file_path, arcname)
    
    size = os.path.getsize(zip_path) / (1024 * 1024)
    print_success(f"Instalador Windows creado: {zip_path} ({size:.2f} MB)")
    return True

def create_linux_installer():
    """Crea el instalador para Linux"""
    print_info("Generando instalador Linux...")
    
    # Copiar el ejecutable compilado en Linux
    if os.path.isfile("dist/Organizador/Organizador"):
        os.makedirs("instaladores_ready", exist_ok=True)
        
        # Crear carpeta temporal
        temp_dir = "temp_linux_build"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        os.makedirs(f"{temp_dir}/Organizador-Linux-v1.0.0")
        
        # Copiar el ejecutable
        shutil.copy("dist/Organizador/Organizador", 
                   f"{temp_dir}/Organizador-Linux-v1.0.0/")
        
        # Copiar el script de instalación
        shutil.copy("install_linux.sh", 
                   f"{temp_dir}/Organizador-Linux-v1.0.0/")
        
        # Copiar archivos necesarios
        for folder in ["src", "assets", "data", "config"]:
            if os.path.exists(folder):
                shutil.copytree(folder, 
                              f"{temp_dir}/Organizador-Linux-v1.0.0/{folder}")
        
        for file in ["requirements.txt", "README.md", "run.py"]:
            if os.path.exists(file):
                shutil.copy(file, f"{temp_dir}/Organizador-Linux-v1.0.0/")
        
        # Crear tarball
        tar_path = "instaladores_ready/Organizador-Linux-v1.0.0.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(f"{temp_dir}/Organizador-Linux-v1.0.0", 
                   arcname="Organizador-Linux-v1.0.0")
        
        # Limpiar
        shutil.rmtree(temp_dir)
        
        size = os.path.getsize(tar_path) / (1024 * 1024)
        print_success(f"Instalador Linux creado: {tar_path} ({size:.2f} MB)")
        return True
    else:
        print_error("No se encontró ejecutable Linux compilado")
        return False

def list_installers():
    """Lista los instaladores creados"""
    print_header("Instaladores Disponibles")
    
    if os.path.exists("instaladores_ready"):
        files = os.listdir("instaladores_ready")
        if files:
            for file in sorted(files):
                path = os.path.join("instaladores_ready", file)
                size = os.path.getsize(path) / (1024 * 1024)
                print(f"  📦 {file:50} ({size:7.2f} MB)")
        else:
            print_error("No hay instaladores en la carpeta instaladores_ready")
    else:
        print_error("Carpeta instaladores_ready no existe")

def main():
    print_header("Generador de Instaladores - Organizador v1.0.0")
    
    print_info("Sistema operativo detectado: Linux")
    print_info("Versión de Python: 3.11+")
    
    # Verificar que existe la compilación
    if not check_dist_exists():
        sys.exit(1)
    
    # Crear instaladores
    windows_ok = create_windows_installer()
    linux_ok = create_linux_installer()
    
    # Listar instaladores
    list_installers()
    
    # Resumen
    print_header("✓ Generación Completada")
    
    if windows_ok:
        print(f"{GREEN}Windows:{RESET} Archivo .zip listo para distribuir")
    if linux_ok:
        print(f"{GREEN}Linux:{RESET} Script .sh + ejecutable compilado")
    
    print(f"""
{YELLOW}Próximos pasos:{RESET}

1. {YELLOW}Para Windows:{RESET}
   - Descargar instaladores_ready/Organizador-Windows-v1.0.0.zip
   - Ejecutar con doble clic
   - Instalar Python 3.7+ si es necesario

2. {YELLOW}Para Linux:{RESET}
   - sudo bash install_linux.sh (desde la carpeta raíz)
   - O ejecutar el binario: ./dist/Organizador/Organizador

3. {YELLOW}Distribuir:{RESET}
   - Subir a GitHub Releases
   - Compartir por email o USB
   - Publicar en sitios de descargas
""")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)
