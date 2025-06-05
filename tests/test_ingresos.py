import sys
import types
import os
from unittest.mock import patch

# Crear modulos falsos para permitir la importacion de ingresos
if 'model' not in sys.modules:
    sys.modules['model'] = types.ModuleType('model')
if 'model.data_manager' not in sys.modules:
    dummy_dm = types.ModuleType('model.data_manager')
    dummy_dm.cargar_datos = lambda *args, **kwargs: []
    dummy_dm.obtener_estadisticas_concepto = lambda concepto: {}
    dummy_dm.cargar_historial_conceptos = lambda: []
    sys.modules['model.data_manager'] = dummy_dm

# Asegurar que la carpeta principal esté en sys.path para poder importar 'ingresos'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import ingresos


def test_calculos_ingresos():
    sample_data = [
        (1, 'Salario', 2000.0, '2024-03-01'),
        (2, 'Freelance', 1500.0, '2024-03-05'),
        (3, 'Nulo', None, '2024-03-10'),
        (4, 'Negativo', -50.0, '2024-03-11'),
    ]
    with patch('ingresos.cargar_datos', return_value=sample_data):
        assert ingresos.calcular_total_ingresos() == 3500.0
        assert ingresos.obtener_ingresos_por_concepto('Salario') == [(1, 'Salario', 2000.0, '2024-03-01')]

