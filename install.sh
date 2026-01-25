#!/bin/bash
# Script de instalación y ejecución optimizado para sistemas con pocos recursos
# Compatible con Linux Mint, Ubuntu, Debian y similares

echo "🚀 Instalador Organizador de Gastos (Optimizado para Sistemas Antiguos)"
echo "========================================================================="
echo ""

# Detectar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    echo "Para Debian/Ubuntu: sudo apt install python3"
    echo "Para Linux Mint: sudo apt install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION detectado"
echo ""

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✅ Entorno virtual creado"
else
    echo "✅ Entorno virtual ya existe"
fi

echo ""
echo "📥 Instalando dependencias (esto puede tomar unos minutos)..."
source venv/bin/activate

# Actualizar pip para seguridad y rendimiento
pip install --upgrade pip setuptools wheel -q

# Instalar dependencias desde requirements.txt
pip install -r requirements.txt -q

if [ $? -eq 0 ]; then
    echo "✅ Dependencias instaladas correctamente"
else
    echo "⚠️  Advertencia: Algunos paquetes podrían no haberse instalado correctamente"
    echo "   Intentando continuar..."
fi

echo ""
echo "========================================================================="
echo "✅ Instalación completada"
echo ""
echo "Para ejecutar la aplicación:"
echo "  Linux/Mac: ./run.sh"
echo "  Windows:   run.bat"
echo ""
echo "O directamente: python3 start_app.py"
echo "========================================================================="
