#!/usr/bin/env python3
"""
Script de construcción para crear instaladores de Organizador
Genera ejecutables y instaladores para Windows y Linux
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

class BuildManager:
    """Gestor para construir y empaquetar la aplicación"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.spec_file = self.project_root / "organizador.spec"
        
    def print_header(self, text):
        """Imprime un encabezado formateado"""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
        
    def print_step(self, text):
        """Imprime un paso del proceso"""
        print(f"► {text}")
        
    def print_success(self, text):
        """Imprime un mensaje de éxito"""
        print(f"✓ {text}")
        
    def print_error(self, text):
        """Imprime un mensaje de error"""
        print(f"✗ {text}")
        
    def clean_build_dirs(self):
        """Limpia directorios de compilación previos"""
        self.print_step("Limpiando directorios previos...")
        
        for directory in [self.dist_dir, self.build_dir]:
            if directory.exists():
                shutil.rmtree(directory)
                self.print_success(f"Directorio {directory.name} eliminado")
                
    def build_executable(self):
        """Construye el ejecutable usando PyInstaller"""
        self.print_header("CONSTRUYENDO EJECUTABLE")
        self.print_step("Compilando aplicación con PyInstaller...")
        
        try:
            # Comando para PyInstaller
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                str(self.spec_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.print_error("Error compilando ejecutable")
                print(result.stderr)
                return False
                
            self.print_success("Ejecutable compilado exitosamente")
            return True
            
        except Exception as e:
            self.print_error(f"Error: {e}")
            return False
            
    def verify_executable(self):
        """Verifica que el ejecutable se creó correctamente"""
        self.print_step("Verificando ejecutable...")
        
        system = platform.system()
        if system == "Windows":
            exe_path = self.dist_dir / "Organizador" / "Organizador.exe"
        else:
            exe_path = self.dist_dir / "Organizador" / "Organizador"
            
        if exe_path.exists():
            self.print_success(f"Ejecutable verificado: {exe_path}")
            return True
        else:
            self.print_error("Ejecutable no encontrado")
            return False
            
    def create_installer_windows(self):
        """Crea un instalador para Windows"""
        self.print_header("CREANDO INSTALADOR PARA WINDOWS")
        
        nsi_file = self.project_root / "installer" / "organizador.nsi"
        
        if not nsi_file.exists():
            self.print_error(f"Archivo NSIS no encontrado: {nsi_file}")
            return False
            
        self.print_step("Para crear el instalador de Windows, necesitas NSIS instalado")
        self.print_step("Descarga NSIS desde: https://nsis.sourceforge.io/")
        self.print_step("")
        self.print_step("Una vez instalado NSIS, ejecuta:")
        print(f"  makensis.exe {str(nsi_file)}")
        print("")
        
        return True
        
    def create_installer_linux(self):
        """Crea un paquete instalable para Linux"""
        self.print_header("CREANDO SCRIPT DE INSTALACIÓN PARA LINUX")
        
        install_script = self.project_root / "install_linux.sh"
        
        if install_script.exists():
            # Hacer el script ejecutable
            os.chmod(install_script, 0o755)
            self.print_success(f"Script instalable listo: {install_script}")
            
            self.print_step("Para instalar en Linux, ejecuta:")
            print(f"  chmod +x {str(install_script)}")
            print(f"  sudo bash {str(install_script)}")
            print("")
            
            return True
        else:
            self.print_error(f"Script de instalación no encontrado: {install_script}")
            return False
            
    def create_package_info(self):
        """Crea archivo de información del paquete"""
        self.print_step("Creando archivo de información del paquete...")
        
        info_file = self.dist_dir / "INSTALACION.txt"
        
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("""
╔════════════════════════════════════════════════════════════╗
║            ORGANIZADOR - GESTOR FINANCIERO PERSONAL        ║
║                     Versión 1.0.0                          ║
╚════════════════════════════════════════════════════════════╝

INSTRUCCIONES DE INSTALACIÓN
═════════════════════════════

PARA WINDOWS:
────────────
1. Descarga el archivo "Organizador-Installer.exe"
2. Haz doble clic para ejecutar el instalador
3. Sigue las instrucciones en pantalla
4. Se creará automáticamente un acceso directo en el escritorio
5. ¡Listo! Abre el acceso directo para ejecutar la aplicación

PARA LINUX:
──────────
1. Abre una terminal en la carpeta del instalador
2. Ejecuta: sudo bash install_linux.sh
3. Espera a que finalice la instalación
4. Se creará un acceso directo en el escritorio
5. ¡Listo! Ejecuta "organizador" desde la terminal o usa el acceso directo

REQUISITOS:
───────────
- Windows: Windows 7 o posterior
- Linux: Python 3.7+ (incluido en la mayoría de distribuciones)
- Espacio en disco: Aproximadamente 500 MB

CARACTERÍSTICAS:
────────────────
✓ Gestión de gastos e ingresos
✓ Seguimiento de ahorros
✓ Análisis de categorías
✓ Cotización de dólares en tiempo real
✓ Simulador de conversión de divisas
✓ Presupuesto inteligente con IA
✓ Exportación de datos
✓ Interfaz amigable con tema claro/oscuro

DESINSTALACIÓN:
───────────────
Windows: Abre "Panel de Control" → "Programas" → "Desinstalar un programa" 
         → Selecciona "Organizador" → "Desinstalar"

Linux:   sudo rm -rf /opt/organizador
         sudo rm /usr/local/bin/organizador

SOPORTE:
────────
Para reportar problemas o sugerencias, contacta a:
Whiterman - whiterman1@gmail.com

GitHub: https://github.com/AlanDi123/Organizador

═════════════════════════════════════════════════════════════
¡Gracias por usar Organizador! 💰
═════════════════════════════════════════════════════════════
""")
        
        self.print_success(f"Información creada: {info_file}")
        
    def create_summary(self):
        """Crea un resumen de la compilación"""
        self.print_header("RESUMEN DE COMPILACIÓN")
        
        summary = f"""
Proyecto: Organizador v1.0.0
Fecha: {Path('run.py').stat().st_mtime}
Sistema: {platform.system()}

ARCHIVOS GENERADOS:
───────────────────
"""
        
        # Enumerar archivos en dist
        if self.dist_dir.exists():
            for root, dirs, files in os.walk(self.dist_dir):
                level = root.replace(str(self.dist_dir), '').count(os.sep)
                indent = ' ' * 2 * (level + 1)
                rel_path = os.path.relpath(root, self.dist_dir)
                summary += f"\n{indent}📁 {rel_path}/\n"
                
                sub_indent = ' ' * 2 * (level + 2)
                for file in files[:10]:  # Mostrar primeros 10 archivos
                    summary += f"{sub_indent}📄 {file}\n"
                    
                if len(files) > 10:
                    summary += f"{sub_indent}... y {len(files) - 10} archivos más\n"
                    
        print(summary)
        
    def main(self):
        """Función principal del proceso de compilación"""
        try:
            self.print_header("INICIANDO COMPILACIÓN DE INSTALADORES")
            
            # 1. Limpiar compilaciones previas
            self.clean_build_dirs()
            
            # 2. Construir ejecutable
            if not self.build_executable():
                return False
                
            # 3. Verificar ejecutable
            if not self.verify_executable():
                return False
                
            # 4. Crear información del paquete
            self.create_package_info()
            
            # 5. Crear resumen
            self.create_summary()
            
            # 6. Instrucciones para instaladores
            if platform.system() == "Windows":
                self.create_installer_windows()
            else:
                self.create_installer_linux()
                
            # Mensaje final
            self.print_header("COMPILACIÓN EXITOSA ✓")
            print("""
Los archivos compilados se encuentran en: dist/Organizador/

PRÓXIMOS PASOS:
──────────────
1. Para Windows: Instala NSIS y ejecuta
   makensis.exe installer/organizador.nsi

2. Para Linux: Ejecuta
   sudo bash install_linux.sh

Los instaladores estarán listos para distribuir.
""")
            return True
            
        except Exception as e:
            self.print_error(f"Error durante la compilación: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    builder = BuildManager()
    success = builder.main()
    sys.exit(0 if success else 1)
