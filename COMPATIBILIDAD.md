# 🖥️ Guía de Compatibilidad Multiplataforma

## Sistemas Operativos Soportados

| Sistema | Versión | Estado | Notas |
|---------|---------|--------|-------|
| **Linux Mint** | 19.0+ | ✅ Excelente | Totalmente optimizado |
| **Ubuntu** | 18.04+ | ✅ Excelente | Mismo que Debian base |
| **Debian** | 9+ | ✅ Excelente | Recomendado para sistemas antiguos |
| **Windows** | 7 SP1+ | ✅ Compatible | Requiere Python 3.9+ |
| **Windows** | 10/11 | ✅ Excelente | Máxima compatibilidad |
| **macOS** | 10.12+ | ✅ Compatible | Intel y Apple Silicon |

## Requisitos por Plataforma

### Linux Mint / Ubuntu / Debian

```bash
# Dependencias del sistema (si Python no está instalado)
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3-pip

# Opcional: para mejor experiencia con calendarios
sudo apt install -y tk-dev

# Ejecutar
./run.sh
```

### Windows 7/10/11

1. Descargar Python desde https://www.python.org/downloads/
   - **IMPORTANTE**: Marcar "Add Python to PATH" durante la instalación
   - Elegir Python 3.9 o superior

2. Abrir PowerShell o CMD como Administrador

3. Navegar a la carpeta del proyecto:
   ```powershell
   cd C:\ruta\a\organizador
   ```

4. Ejecutar:
   ```powershell
   run.bat
   ```

### macOS (Intel y M1/M2)

```bash
# Instalar Homebrew (si no lo tienes)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python
brew install python3

# Ejecutar la aplicación
./run.sh
```

## Diferencias de Comportamiento

### 🐧 Linux
- ✅ Mejor rendimiento en hardware antiguo
- ✅ Menor uso de memoria
- ✅ Fuentes y colores más precisos
- ℹ️ Requiere activar virtualenv manualmente a veces

### 🪟 Windows
- ✅ Interfaz más familiar
- ✅ Más fácil de instalar para principiantes
- ⚠️ Requiere Python instalado correctamente
- ℹ️ Algunos atajos de teclado pueden variar

### 🍎 macOS
- ✅ Compatible con Intel y Apple Silicon
- ✅ Integración nativa con el sistema
- ⚠️ Requiere aceptar permisos de seguridad
- ℹ️ Puede ser más lento en hardware antiguo

## Problemas Específicos por Plataforma

### Linux

**Problema**: Fuente extraña o caracteres rotos
```bash
# Solución: Instalar fuentes necesarias
sudo apt install fonts-liberation fonts-dejavu
```

**Problema**: Tecla Alt no funciona para acceder a menús
```bash
# Solución: Es normal en algunos gestores de ventanas. Usar mouse normalmente.
```

**Problema**: Aplicación se congela con tkcalendar
```bash
# Solución: Ya está arreglado en la versión optimizada. Si persiste:
sudo apt install python3-tk
```

### Windows

**Problema**: "Python is not recognized as an internal or external command"
- Solución: Reinstalar Python y marcar "Add Python to PATH"

**Problema**: antivirus bloquea la aplicación
- Solución: Agregar la carpeta del proyecto a excepciones del antivirus

**Problema**: Caracteres especiales (€, ñ, ç) se ven mal
- Solución: Cambiar encoding en `src/utils/utils.py` a UTF-8

### macOS

**Problema**: "Command not found: python3"
```bash
# Solución:
brew install python3
```

**Problema**: No se puede abrir start_app.py
```bash
# Solución: Hacer ejecutable
chmod +x start_app.py
```

## Variables de Entorno (Opcional)

Para poder personalizar el comportamiento de la aplicación, puedes establecer:

```bash
# Linux/macOS
export ORGANIZADOR_THEME=dark          # claro o dark
export ORGANIZADOR_LOG_LEVEL=DEBUG     # DEBUG, INFO, WARNING
export ORGANIZADOR_DATA_PATH=/custom/path  # ruta personalizada

# Windows PowerShell
$env:ORGANIZADOR_THEME="dark"
$env:ORGANIZADOR_LOG_LEVEL="DEBUG"

# Windows CMD
set ORGANIZADOR_THEME=dark
set ORGANIZADOR_LOG_LEVEL=DEBUG
```

## Verificación de Compatibilidad

Ejecuta este comando para verificar que todo esté bien configurado:

```bash
python3 -c "
import sys
import tkinter as tk
import sqlite3
import json

print(f'✅ Python {sys.version}')
print(f'✅ Tkinter disponible')
print(f'✅ SQLite3 disponible')
print(f'✅ JSON disponible')
print('✅ Sistema compatible')
"
```

## Rendimiento Esperado

### En Sistemas Antiguos (eMachines, ~1GB RAM)

- Tiempo de inicio: 2-3 segundos
- Uso de memoria: ~40-60MB
- Uso de CPU: ~5-10% en reposo
- Interfaz responsiva incluso con 500+ registros

### En Sistemas Modernos (4GB+ RAM)

- Tiempo de inicio: <1 segundo
- Uso de memoria: ~80-120MB
- Interfaz muy responsiva
- Rendimiento óptimo

## Actualización Cruzada de Plataformas

Si cambias de sistema operativo, tus datos se transferirán automáticamente:

1. Copia la carpeta `data/` de tu sistema antiguo
2. Pégala en la misma ubicación del proyecto nuevo
3. Ejecuta la aplicación - detectará automáticamente los datos

## Soporte para Arquitecturas ARM

La aplicación es totalmente compatible con:
- ✅ Raspberry Pi (3B+, 4B, 5)
- ✅ NVIDIA Jetson (Nano, Orin)
- ✅ BeagleBone
- ✅ Apple M1/M2 (macOS)

Solo instala Python 3.9+ y ejecuta normalmente.

---

**¿Tu plataforma no está listada? Envía un reporte de compatibilidad.**
