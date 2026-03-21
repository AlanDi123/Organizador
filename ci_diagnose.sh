#!/bin/bash
# Script de diagnóstico para CI/CD
# Verifica que todo esté configurado correctamente antes del build

set -e

echo "========================================="
echo "  Diagnóstico para CI/CD"
echo "========================================="

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ERRORS=0

# Verificar Python
echo -e "\n${YELLOW}Verificando Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python3 no encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Verificar Java
echo -e "\n${YELLOW}Verificando Java...${NC}"
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo -e "${GREEN}✓ $JAVA_VERSION${NC}"
else
    echo -e "${RED}✗ Java no encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Verificar javac
echo -e "\n${YELLOW}Verificando javac...${NC}"
if command -v javac &> /dev/null; then
    JAVAC_VERSION=$(javac -version 2>&1)
    echo -e "${GREEN}✓ $JAVAC_VERSION${NC}"
else
    echo -e "${RED}✗ javac no encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Verificar buildozer.spec
echo -e "\n${YELLOW}Verificando buildozer.spec...${NC}"
if [ -f "buildozer.spec" ]; then
    echo -e "${GREEN}✓ buildozer.spec encontrado${NC}"
    
    # Verificar configuración crítica
    if grep -q "package.domain = org.alandin123" buildozer.spec; then
        echo -e "${GREEN}✓ package.domain configurado${NC}"
    else
        echo -e "${RED}✗ package.domain no configurado${NC}"
        ERRORS=$((ERRORS + 1))
    fi
    
    if grep -q "requirements = python3,kivy" buildozer.spec; then
        echo -e "${GREEN}✓ requirements configurados${NC}"
    else
        echo -e "${RED}✗ requirements no configurados${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗ buildozer.spec no encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Verificar archivos críticos
echo -e "\n${YELLOW}Verificando archivos críticos...${NC}"
CRITICAL_FILES=(
    "main.py"
    "src/mobile/app.py"
    "src/cloud/__init__.py"
    "src/core/__init__.py"
    "requirements.txt"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file no encontrado${NC}"
        ERRORS=$((ERRORS + 1))
    fi
done

# Verificar sintaxis de Python
echo -e "\n${YELLOW}Verificando sintaxis de Python...${NC}"
SYNTAX_ERRORS=0

for file in src/mobile/app.py src/cloud/__init__.py src/core/__init__.py; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            echo -e "${GREEN}✓ $file${NC}"
        else
            echo -e "${RED}✗ $file tiene errores de sintaxis${NC}"
            SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Archivos Python verificados${NC}"
fi

# Resumen
echo -e "\n========================================="
echo -e "  RESUMEN"
echo "========================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Todo está listo para el build!${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Ejecutar: buildozer android debug"
    echo "  2. El APK estará en: bin/"
    exit 0
else
    echo -e "${RED}✗ Se encontraron $ERRORS errores${NC}"
    echo ""
    echo "Por favor corrige los errores antes de continuar."
    exit 1
fi
