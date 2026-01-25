@echo off
REM ============================================================================
REM  ORGANIZADOR v1.0.0 - Windows Launcher
REM  Inicia la aplicación Organizador compilada
REM ============================================================================

setlocal enabledelayedexpansion

REM Obtener directorio del script
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Ejecutar el binario compilado (si está en dist/) o directamente
if exist "dist\Organizador\Organizador.exe" (
    start "" "dist\Organizador\Organizador.exe" %*
) else if exist "Organizador.exe" (
    start "" "Organizador.exe" %*
) else (
    echo.
    echo ════════════════════════════════════════════════════
    echo   ERROR: No se encontró el ejecutable de Organizador
    echo ════════════════════════════════════════════════════
    echo.
    echo Asegúrate de que la carpeta de Organizador contiene:
    echo   - dist\Organizador\Organizador.exe
    echo   - o Organizador.exe en la raíz
    echo.
    pause
    exit /b 1
)

endlocal
