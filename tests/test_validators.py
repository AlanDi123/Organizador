# tests/test_validators.py
"""
Tests para el sistema de validación.
"""

import pytest
from src.utils.validators import Validator, ValidationError


class TestValidator:
    """Tests para la clase Validator"""
    
    def test_valid_amount(self):
        """Prueba validación de montos"""
        assert Validator.is_valid_amount(100) == True
        assert Validator.is_valid_amount(0) == True
        assert Validator.is_valid_amount(999999999) == True
        assert Validator.is_valid_amount(-1) == False
        assert Validator.is_valid_amount("abc") == False
        assert Validator.is_valid_amount(1000000000) == False
    
    def test_valid_category(self):
        """Prueba validación de categorías"""
        assert Validator.is_valid_category("alimentación") == True
        assert Validator.is_valid_category("ab") == False  # Muy corto
        assert Validator.is_valid_category("a" * 51) == False  # Muy largo
        assert Validator.is_valid_category("123") == True
    
    def test_valid_date(self):
        """Prueba validación de fechas"""
        from datetime import datetime
        
        assert Validator.is_valid_date(datetime.now()) == True
        assert Validator.is_valid_date("2024-01-01") == True
        assert Validator.is_valid_date("invalid") == False
        assert Validator.is_valid_date(None) == False
    
    def test_sanitize_input(self):
        """Prueba sanitización de entrada"""
        assert Validator.sanitize_input("  hello  ") == "hello"
        assert Validator.sanitize_input("a" * 300, max_length=100) == "a" * 100


class TestValidateGasto:
    """Tests para validación de gastos"""
    
    def test_valid_gasto(self):
        """Prueba validación de gasto válido"""
        gasto = {
            'monto': 100,
            'categoria': 'alimentación',
            'fecha': '2024-01-01'
        }
        result = Validator.validate_gasto(gasto)
        assert result == True
    
    def test_missing_fields(self):
        """Prueba validación con campos faltantes"""
        gasto = {'monto': 100}
        result = Validator.validate_gasto(gasto)
        assert result != True
        assert isinstance(result, str)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
