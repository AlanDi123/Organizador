@echo off
REM Script para ejecutar la aplicación en Windows
REM Compatible con Python 3.8+

echo Organizador de Gastos - Versión Optimizada
echo ============================================
echo.

REM Verificar si existe venv
if not exist "venv\" (
    echo Creando entorno virtual...
    python -m venv venv
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Ejecutar la aplicación
python start_app.py
