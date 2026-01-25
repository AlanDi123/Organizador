#!/usr/bin/env python
import sys
import os

print("Intentando importar ia_module...")
sys.stdout.flush()

try:
    from src.models import ia_module
    print("✅ Módulo importado")
    sys.stdout.flush()
    
    print("Creando instancia...")
    sys.stdout.flush()
    modulo = ia_module.ModuloIA()
    print("✅ Instancia creada correctamente")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    traceback.print_exc()
