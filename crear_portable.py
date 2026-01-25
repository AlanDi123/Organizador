#!/usr/bin/env python3
"""
Generador rápido de instaladores portables para Organizador
Crea paquetes ZIP listos para distribuir sin necesidad de NSIS o compilación larga
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

class PortableBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.output_dir = self.project_root / "instaladores_ready"
        
    def create_portable_package(self):
        """Crea un paquete portable listo para usar"""
        print("\n╔════════════════════════════════════════════════════╗")
        print("║  Generador de Paquete Portable - Organizador 1.0.0  ║")
        print("╚════════════════════════════════════════════════════╝\n")
        
        # Crear directorio de salida
        self.output_dir.mkdir(exist_ok=True)
        
        # Crear paquete portable
        print("► Creando paquete portable...")
        portable_dir = self.output_dir / "Organizador-Portable-v1.0.0"
        portable_dir.mkdir(exist_ok=True)
        
        # Copiar aplicación
        print("  - Copiando archivos de aplicación...")
        src_dirs = ['src', 'assets', 'data', 'config']
        for src_dir in src_dirs:
            src_path = self.project_root / src_dir
            if src_path.exists():
                dst_path = portable_dir / src_dir
                if dst_path.exists():
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
        
        # Copiar archivos principales
        for file in ['run.py', 'requirements.txt', 'README.md']:
            src_file = self.project_root / file
            if src_file.exists():
                shutil.copy(src_file, portable_dir / file)
        
        # Crear scripts de ejecución
        print("  - Creando scripts de ejecución...")
        self._create_run_scripts(portable_dir)
        
        # Crear instrucciones
        print("  - Creando instrucciones...")
        self._create_instructions(portable_dir)
        
        # Crear archivo comprimido
        print("  - Comprimiendo paquete...")
        zip_path = self.output_dir / "Organizador-Portable-v1.0.0"
        shutil.make_archive(str(zip_path), 'zip', portable_dir.parent, portable_dir.name)
        
        print(f"\n✓ Paquete portable creado: {zip_path}.zip\n")
        
        # Información de distribución
        self._print_distribution_info()
        
        return True
    
    def _create_run_scripts(self, target_dir):
        """Crea scripts para ejecutar la aplicación"""
        
        # Script para Windows
        batch_script = target_dir / "Organizador.bat"
        batch_script.write_text("""@echo off
REM Ejecutar Organizador en Windows

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python no está instalado o no está en el PATH
    echo.
    echo Para instalar Python:
    echo 1. Descarga desde: https://www.python.org/downloads/
    echo 2. Durante la instalación, marca "Add Python to PATH"
    echo 3. Reinicia tu computadora
    echo 4. Intenta ejecutar Organizador nuevamente
    echo.
    pause
    exit /b 1
)

REM Instalar dependencias (solo la primera vez)
if not exist venv (
    echo Instalando dependencias (primera ejecución)...
    python -m pip install -q -r requirements.txt
)

REM Ejecutar la aplicación
echo Iniciando Organizador...
python run.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Hubo un problema al ejecutar la aplicación
    echo Por favor, intenta nuevamente o contacta al soporte
    echo.
    pause
)
""")
        
        # Script para Linux/Mac
        bash_script = target_dir / "Organizador.sh"
        bash_script.write_text("""#!/bin/bash

# Ejecutar Organizador en Linux/Mac

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo ""
    echo "ERROR: Python 3 no está instalado"
    echo ""
    echo "Para instalar Python 3:"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "Fedora: sudo dnf install python3"
    echo "Mac: brew install python3"
    echo ""
    exit 1
fi

# Instalar dependencias (solo la primera vez)
if [ ! -d "venv" ]; then
    echo "Instalando dependencias (primera ejecución)..."
    python3 -m pip install -q -r requirements.txt
fi

# Ejecutar la aplicación
echo "Iniciando Organizador..."
python3 run.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Hubo un problema al ejecutar la aplicación"
    echo "Por favor, intenta nuevamente o contacta al soporte"
    echo ""
fi
""")
        
        # Hacer el script bash ejecutable
        bash_script.chmod(0o755)
    
    def _create_instructions(self, target_dir):
        """Crea archivo de instrucciones de instalación"""
        
        instructions = target_dir / "COMO_INSTALAR.txt"
        instructions.write_text("""
╔═══════════════════════════════════════════════════════════════╗
║      ORGANIZADOR - Gestor Financiero Personal v1.0.0         ║
║              INSTRUCCIONES DE INSTALACIÓN                    ║
╚═══════════════════════════════════════════════════════════════╝

INSTALACIÓN RÁPIDA (SIN COMPILACIÓN)
═════════════════════════════════════

Esta es una versión PORTABLE que se ejecuta directamente sin 
necesidad de instalar nada en el sistema.

REQUISITOS:
───────────
• Python 3.7 o superior
• Acceso a Internet (para descargar dependencias la primera vez)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PARA WINDOWS:
═════════════

Paso 1: Descargar Python
────────────────────────
1. Abre: https://www.python.org/downloads/
2. Descarga la última versión (3.11+)
3. ¡IMPORTANTE! Marca "Add Python to PATH" durante la instalación
4. Termina la instalación

Paso 2: Ejecutar la aplicación
────────────────────────────────
1. Abre la carpeta "Organizador" (esta carpeta)
2. Haz doble clic en "Organizador.bat"
3. La primera vez tardará unos segundos instalando dependencias
4. ¡Listo! La aplicación se ejecutará

Paso 3: Crear Acceso Directo (Opcional)
───────────────────────────────────────
1. Haz clic derecho en "Organizador.bat"
2. Selecciona "Enviar a" > "Escritorio (crear acceso directo)"
3. Abre la aplicación desde el acceso directo

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PARA LINUX / MAC:
═════════════════

Paso 1: Verificar Python
────────────────────────
Abre terminal y ejecuta:
  python3 --version

Si no está instalado:
  Ubuntu/Debian: sudo apt install python3 python3-pip
  Fedora: sudo dnf install python3
  Mac: brew install python3

Paso 2: Ejecutar la aplicación
────────────────────────────────
Abre terminal en esta carpeta y ejecuta:
  ./Organizador.sh

O:
  bash Organizador.sh

La primera vez tardará unos segundos instalando dependencias.

Paso 3: Crear Acceso Directo (Opcional)
───────────────────────────────────────
Ejecuta en terminal:
  ln -s "$(pwd)/Organizador.sh" ~/Desktop/Organizador
  chmod +x ~/Desktop/Organizador

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CARACTERÍSTICAS:
════════════════
✓ Gestión de gastos e ingresos
✓ Seguimiento de ahorros independiente
✓ Análisis de categorías
✓ Cotización de dólares en tiempo real
✓ Simulador de conversión de divisas
✓ Sistema inteligente de presupuesto
✓ Exportación de datos
✓ Interfaz amigable
✓ Funciona offline (sin conexión después de la instalación)

ESTRUCTURA DE CARPETAS:
══════════════════════
Organizador/
├── Organizador.bat          (Ejecutable para Windows)
├── Organizador.sh           (Ejecutable para Linux/Mac)
├── run.py                   (Archivo principal Python)
├── requirements.txt         (Dependencias)
├── COMO_INSTALAR.txt       (Este archivo)
├── src/                     (Código fuente)
├── assets/                  (Recursos/Iconos)
├── data/                    (Datos de la aplicación)
└── config/                  (Configuración)

SOLUCIÓN DE PROBLEMAS:
══════════════════════

WINDOWS - "No se reconoce el comando 'python'"
  → Python no está en el PATH
  → Solución: Reinstala Python y marca "Add to PATH"
  → Reinicia la computadora después

WINDOWS - El archivo .bat no se abre
  → Abre cmd en la carpeta y ejecuta: Organizador.bat
  → Verifica que Python esté correctamente instalado

LINUX - "Permission denied"
  Ejecuta:
  chmod +x Organizador.sh
  ./Organizador.sh

LINUX - "Python not found"
  → Instala Python: sudo apt install python3 python3-pip
  → En algunos sistemas usa "python3" en lugar de "python"

TODOS - Errores de módulos faltantes
  → La aplicación intenta instalarlos automáticamente
  → Si falla, abre terminal y ejecuta:
    Windows: python -m pip install -r requirements.txt
    Linux: python3 -m pip install -r requirements.txt

ACCESO A LOS DATOS:
═══════════════════
Los datos se guardan localmente en:
  Windows: data/ folder (dentro de Organizador)
  Linux/Mac: data/ folder (dentro de Organizador)

No necesitas conexión a Internet para usar la aplicación
después de la instalación inicial.

ACTUALIZAR LA APLICACIÓN:
═════════════════════════
1. Descarga la nueva versión
2. Copia la carpeta "Organizador" reemplazando la antigua
3. Mantén la carpeta "data/" con tus datos antiguos

CONTACTO Y SOPORTE:
═══════════════════
• Email: whiterman1@gmail.com
• GitHub: https://github.com/AlanDi123/Organizador
• Problemas: https://github.com/AlanDi123/Organizador/issues

VERSIÓN Y INFORMACIÓN:
══════════════════════
Organizador v1.0.0
Última actualización: Enero 2026
Autor: Whiterman

═══════════════════════════════════════════════════════════════
¡Gracias por usar Organizador! 💰
═══════════════════════════════════════════════════════════════
""")
    
    def _print_distribution_info(self):
        """Imprime información de distribución"""
        
        print("╔════════════════════════════════════════════════════╗")
        print("║       ✓ PAQUETE PORTABLE LISTO PARA USAR          ║")
        print("╚════════════════════════════════════════════════════╝\n")
        
        print("📦 Archivo creado:")
        print(f"   {self.output_dir}/Organizador-Portable-v1.0.0.zip\n")
        
        print("📋 Contenido del paquete:")
        print("   ✓ Código fuente completo")
        print("   ✓ Scripts para Windows (Organizador.bat)")
        print("   ✓ Scripts para Linux/Mac (Organizador.sh)")
        print("   ✓ Instrucciones de instalación")
        print("   ✓ Archivo de requisitos (requirements.txt)\n")
        
        print("🚀 Cómo usar:")
        print("   Windows: Descomprime y ejecuta Organizador.bat")
        print("   Linux/Mac: Descomprime y ejecuta ./Organizador.sh\n")
        
        print("⚡ Ventajas de esta versión:")
        print("   • No requiere compilación")
        print("   • Funciona en Windows, Linux y Mac")
        print("   • Solo necesita Python 3.7+")
        print("   • Instala dependencias automáticamente\n")
        
        print("📥 Distribución:")
        print("   Puedes compartir el archivo .zip con cualquiera")
        print("   que tenga Python instalado\n")
        
        print("═" * 60)
        print("\n✓ ¡Listo para distribuir!\n")

if __name__ == "__main__":
    builder = PortableBuilder()
    builder.create_portable_package()
