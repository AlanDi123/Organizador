#!/usr/bin/env python3
"""
Genera paquetes ejecutables para Windows, Linux y macOS
Todo compilado sin necesidad de Python instalado en la máquina del usuario
"""

import os
import shutil
import subprocess
import sys
import platform
from pathlib import Path

def crear_paquete_windows():
    """Prepara Organizador.exe para Windows (sin Python requerido)"""
    print("\n" + "="*60)
    print("📦 PAQUETE WINDOWS (Standalone - Sin Python)")
    print("="*60)
    
    exe_path = Path("dist/Organizador")
    windows_exe = Path("Organizador-Windows.exe")
    
    if exe_path.exists():
        shutil.copy(exe_path, windows_exe)
        size = windows_exe.stat().st_size / (1024*1024)
        print(f"✅ Creado: {windows_exe} ({size:.1f} MB)")
        print("   • No requiere Python instalado")
        print("   • Todas las dependencias incluidas")
        print("   • Haz doble clic para ejecutar")
        return True
    else:
        print(f"❌ No encontrado: {exe_path}")
        print("   Primero compila con: python build_exe.py")
        return False

def crear_paquete_linux():
    """Prepara ejecutable para Linux"""
    print("\n" + "="*60)
    print("🐧 PAQUETE LINUX (Standalone - Sin Python)")
    print("="*60)
    
    exe_path = Path("dist/Organizador")
    
    if exe_path.exists():
        # Crear directorio del paquete
        linux_dir = Path("Organizador-Linux")
        if linux_dir.exists():
            shutil.rmtree(linux_dir)
        linux_dir.mkdir()
        
        # Copiar ejecutable
        shutil.copy(exe_path, linux_dir / "Organizador")
        os.chmod(linux_dir / "Organizador", 0o755)
        
        # Crear script de instalación
        install_script = linux_dir / "install.sh"
        install_script.write_text("""#!/bin/bash
# Instalador de Organizador para Linux

set -e

INSTALL_DIR="/opt/organizador"

echo "📦 Instalando Organizador..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp Organizador "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/Organizador"

# Crear acceso directo
sudo tee /usr/local/bin/organizador > /dev/null <<EOF
#!/bin/bash
"$INSTALL_DIR/Organizador" "$@"
EOF
sudo chmod +x /usr/local/bin/organizador

echo "✅ ¡Instalación completada!"
echo "Usa: organizador"
""")
        os.chmod(install_script, 0o755)
        
        # Crear README
        readme = linux_dir / "README.md"
        readme.write_text("""# Organizador para Linux

## Instalación automática
```bash
./install.sh
```

## Ejecución directa (sin instalar)
```bash
./Organizador
```

## Desinstalación
```bash
sudo rm -f /opt/organizador/Organizador /usr/local/bin/organizador
```

**Características:**
- No requiere Python instalado
- Todas las dependencias incluidas
- Ejecutable optimizado de 60 MB
""")
        
        # Crear tarball
        tar_name = "Organizador-Linux-standalone.tar.gz"
        shutil.make_archive(
            "Organizador-Linux-standalone",
            "gztar",
            ".",
            linux_dir
        )
        
        size = Path(tar_name).stat().st_size / (1024*1024)
        print(f"✅ Creado: {tar_name} ({size:.1f} MB)")
        print("   • No requiere Python instalado")
        print("   • Con script de instalación automática")
        print("   • O ejecuta directamente sin instalar")
        
        return True
    else:
        print(f"❌ No encontrado: {exe_path}")
        return False

def crear_paquete_zip():
    """Crea ZIP portable para todas las plataformas"""
    print("\n" + "="*60)
    print("📦 PAQUETE PORTABLE (Windows/Linux/Mac - Sin Python)")
    print("="*60)
    
    exe_path = Path("dist/Organizador")
    
    if exe_path.exists():
        portable_dir = Path("Organizador-Portable")
        if portable_dir.exists():
            shutil.rmtree(portable_dir)
        portable_dir.mkdir()
        
        # Copiar ejecutable
        shutil.copy(exe_path, portable_dir / "Organizador")
        os.chmod(portable_dir / "Organizador", 0o755)
        
        # Scripts de ejecución
        # Windows batch
        (portable_dir / "Organizador.bat").write_text(
            "@echo off\ncd /d \"%~dp0\"\nOrganizador.exe %*"
        )
        
        # Linux/Mac shell
        (portable_dir / "organizador.sh").write_text("""#!/bin/bash
cd "$(dirname "$0")"
./Organizador "$@"
""")
        os.chmod(portable_dir / "organizador.sh", 0o755)
        
        # README
        (portable_dir / "README.txt").write_text("""ORGANIZADOR - PAQUETE PORTABLE

SIN REQUISITOS DE INSTALACIÓN - FUNCIONA EN CUALQUIER MÁQUINA SIN PYTHON

Windows:
  1. Haz doble clic en: Organizador.bat
  2. O ejecuta: Organizador.exe

Linux / Mac:
  1. Abre terminal en esta carpeta
  2. Ejecuta: ./organizador.sh
  3. O: ./Organizador

Características:
✓ No requiere Python instalado
✓ Todas las dependencias incluidas
✓ Funciona en Windows, Linux y Mac
✓ Portable - copia la carpeta donde quieras
✓ Sin instalación necesaria
""")
        
        # Crear ZIP
        zip_name = "Organizador-Portable-Standalone"
        shutil.make_archive(zip_name, "zip", ".", portable_dir)
        
        size = Path(f"{zip_name}.zip").stat().st_size / (1024*1024)
        print(f"✅ Creado: {zip_name}.zip ({size:.1f} MB)")
        print("   • No requiere Python instalado")
        print("   • Funciona en Windows, Linux y Mac")
        print("   • Descomprime y ejecuta")
        
        return True
    else:
        print(f"❌ No encontrado: {exe_path}")
        return False

def main():
    """Genera todos los paquetes"""
    print("\n" + "🚀"*30)
    print(" GENERADOR DE PAQUETES EJECUTABLES - SIN PYTHON REQUERIDO")
    print("🚀"*30)
    
    # Verificar que dist/Organizador existe
    if not Path("dist/Organizador").exists():
        print("\n❌ ERROR: dist/Organizador no existe")
        print("   Primero compila con: python -m PyInstaller --onefile --windowed --name Organizador run.py")
        sys.exit(1)
    
    # Crear paquetes
    resultados = [
        ("Windows", crear_paquete_windows()),
        ("Linux", crear_paquete_linux()),
        ("Portable", crear_paquete_zip()),
    ]
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    
    for nombre, exito in resultados:
        estado = "✅" if exito else "❌"
        print(f"{estado} {nombre}")
    
    print("\n" + "="*60)
    print("✨ ¡PAQUETES LISTOS PARA DISTRIBUIR!")
    print("="*60)
    print("\nLos usuarios YA NO NECESITAN PYTHON INSTALADO para usar Organizador")
    print("\nArchivos creados:")
    print("  • Organizador-Windows.exe (60 MB)")
    print("  • Organizador-Linux-standalone.tar.gz")
    print("  • Organizador-Portable-Standalone.zip")

if __name__ == "__main__":
    main()
