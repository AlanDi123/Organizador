import sys
import types
import os
from unittest.mock import patch

# Crear modulos falsos para permitir la importacion de gastos
if 'model' not in sys.modules:
    sys.modules['model'] = types.ModuleType('model')
if 'model.data_manager' not in sys.modules:
    dummy_dm = types.ModuleType('model.data_manager')
    dummy_dm.cargar_datos = lambda *args, **kwargs: []
    sys.modules['model.data_manager'] = dummy_dm

# Asegurar que la carpeta principal esté en sys.path para poder importar 'gastos'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import gastos


def test_calculos_gastos():
    sample_data = [
        (1, 'Alquiler', 1000.0, True, '2024-03-01'),
        (2, 'Comida', 500.0, False, '2024-03-02'),
        (3, 'Nulo', None, True, '2024-03-03'),
        (4, 'Negativo', -20.0, False, '2024-03-04'),
        (5, 'Luz', 200.0, True, '2024-03-05'),
    ]
    with patch('gastos.cargar_datos', return_value=sample_data):
        assert gastos.calcular_total_gastos() == 1700.0
        assert gastos.calcular_gastos_recurrentes() == 1200.0
        assert gastos.calcular_gastos_no_recurrentes() == 500.0
