#!/bin/bash
# Ejecutar Organizador compilado en Linux

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Ejecutar el binario compilado
exec ./dist/Organizador/Organizador "$@"
