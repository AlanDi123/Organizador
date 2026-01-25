#!/usr/bin/env python3
"""
Script de inicio optimizado para sistemas con pocos recursos (Linux Mint, eMachines, 1GB RAM).
Compatible con Windows y Linux.
"""

import os
import sys
import gc

# Activar garbage collection agresivo para sistemas con pocos recursos
gc.set_threshold(700, 10, 10)

# Agregar la raíz del proyecto al path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Desactivalizar algunas características pesadas de matplotlib si es posible
import matplotlib
matplotlib.use('TkAgg')

# Importar y ejecutar la aplicación
try:
    from src.views.main_app import main
    main()
except Exception as e:
    print(f"❌ Error al iniciar la aplicación: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
