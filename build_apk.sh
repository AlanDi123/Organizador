#!/bin/bash
# Script para compilar el APK Android usando Buildozer
# Actualizado para manejar entornos Python gestionados externamente (PEP 668)

set -e

echo "========================================="
echo "  Compilador de APK - Organizador"
echo "========================================="

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detectar si estamos en un entorno virtual
IN_VENV=false
if [ -n "$VIRTUAL_ENV" ]; then
    IN_VENV=true
    echo -e "${GREEN}✓ Entorno virtual detectado: $VIRTUAL_ENV${NC}"
fi

# Verificar si buildozer está instalado
if ! command_exists buildozer; then
    echo -e "${YELLOW}Buildozer no está instalado.${NC}"
    
    # Opción 1: Intentar con pipx (recomendado para apps)
    if command_exists pipx; then
        echo -e "${GREEN}pipx encontrado. Instalando buildozer con pipx...${NC}"
        pipx install buildozer
        echo -e "${GREEN}✓ Buildozer instalado con pipx${NC}"
        echo -e "${YELLOW}Nota: Usando buildozer desde pipx${NC}"
    # Opción 2: Crear entorno virtual si no estamos en uno
    elif [ "$IN_VENV" = false ]; then
        echo -e "${YELLOW}Creando entorno virtual para buildozer...${NC}"
        
        VENV_DIR=".venv_buildozer"
        if [ ! -d "$VENV_DIR" ]; then
            python3 -m venv "$VENV_DIR"
            echo -e "${GREEN}✓ Entorno virtual creado en $VENV_DIR${NC}"
        fi
        
        # Activar entorno virtual
        source "$VENV_DIR/bin/activate"
        echo -e "${GREEN}✓ Entorno virtual activado${NC}"
        
        # Actualizar pip
        pip install --upgrade pip
        
        # Instalar buildozer
        echo -e "${YELLOW}Instalando buildozer...${NC}"
        pip install buildozer
        
        echo -e "${GREEN}✓ Buildozer instalado en el entorno virtual${NC}"
        echo -e "${YELLOW}Para usar buildozer manualmente, activa el entorno:${NC}"
        echo -e "       source $VENV_DIR/bin/activate"
    # Opción 3: Usar --break-system-packages (último recurso)
    else
        echo -e "${RED}⚠ Usando --break-system-packages (último recurso)${NC}"
        echo -e "${YELLOW}Esto puede afectar tu instalación global de Python${NC}"
        pip install --break-system-packages buildozer
    fi
else
    echo -e "${GREEN}✓ Buildozer ya está instalado${NC}"
fi

# Verificar dependencias del sistema
echo -e "${YELLOW}Verificando dependencias del sistema...${NC}"

MISSING_DEPS=()

# Verificar comandos esenciales
for cmd in git python3 java; do
    if ! command_exists "$cmd"; then
        MISSING_DEPS+=("$cmd")
    fi
done

# Verificar paquetes comunes de desarrollo
if [ "$(uname)" = "Linux" ]; then
    for pkg in autoconf automake build-essential libssl-dev libffi-dev \
               python3-dev libtiff5-dev libjpeg8-dev zlib1g-dev \
               libfreetype6-dev liblcms2-dev libxml2-dev libxslt1-dev \
               wget openjdk-17-jdk; do
        if ! dpkg -l | grep -q "^ii  $pkg "; then
            MISSING_DEPS+=("$pkg")
        fi
    done
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${RED}Faltan dependencias del sistema:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo -e "  - $dep"
    done
    
    echo ""
    echo -e "${YELLOW}¿Quieres instalar las dependencias faltantes? (y/n)${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Instalando dependencias...${NC}"
        sudo apt update
        sudo apt install -y "${MISSING_DEPS[@]}"
        echo -e "${GREEN}✓ Dependencias instaladas${NC}"
    else
        echo -e "${RED}⚠ La compilación podría fallar sin estas dependencias${NC}"
    fi
fi

# Verificar JAVA
if command_exists java; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    echo -e "${GREEN}✓ Java encontrado: versión $JAVA_VERSION${NC}"
    
    if [ "$JAVA_VERSION" -lt 17 ]; then
        echo -e "${YELLOW}⚠ Se recomienda Java 17 o superior para Android${NC}"
    fi
else
    echo -e "${RED}✗ Java no encontrado. La compilación fallará.${NC}"
fi

# Crear directorio bin si no existe
mkdir -p bin

# Limpiar build anterior (opcional)
if [ "$1" == "--clean" ]; then
    echo -e "${YELLOW}Limpiando build anterior...${NC}"
    rm -rf .buildozer
    rm -rf bin
    mkdir -p bin
fi

# Ejecutar buildozer
echo -e "${GREEN}Iniciando compilación del APK...${NC}"
echo "Esto puede tomar varios minutos la primera vez (10-30 min)."
echo ""

# Asegurarnos de usar buildozer desde el PATH correcto
if [ "$IN_VENV" = false ] && [ -d ".venv_buildozer" ]; then
    source ".venv_buildozer/bin/activate"
fi

if [ "$1" == "--release" ]; then
    echo -e "${YELLOW}Compilando APK de RELEASE...${NC}"
    buildozer android release
    echo -e "${GREEN}¡APK de RELEASE compilado!${NC}"
    echo "El APK firmado estará en: bin/"
else
    echo -e "${YELLOW}Compilando APK de DEBUG...${NC}"
    buildozer android debug
    echo -e "${GREEN}¡APK de DEBUG compilado!${NC}"
    echo "El APK estará en: bin/"
fi

# Listar APKs generados
echo ""
echo "========================================="
echo "  APKs generados:"
echo "========================================="
ls -lh bin/*.apk 2>/dev/null || echo -e "${RED}No se encontraron APKs${NC}"

echo ""
echo "========================================="
echo "  Para instalar en tu dispositivo:"
echo "========================================="
echo "1. Conecta tu dispositivo Android vía USB"
echo "2. Habilita 'Depuración USB' en las opciones de desarrollador"
echo "3. Ejecuta: adb install bin/organizador_finanzas-*.apk"
echo ""
echo "O transfiere el APK manualmente e instálalo"
echo "========================================="

# Desactivar entorno virtual si fue activado
if [ "$IN_VENV" = false ] && [ -d ".venv_buildozer" ]; then
    deactivate 2>/dev/null || true
fi
