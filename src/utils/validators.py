# src/utils/validators.py
"""
Sistema de validación robusto para datos de entrada.
"""

from typing import Any, Dict, Optional, Union, List
from datetime import datetime
import re


class ValidationError(Exception):
    """Excepción para errores de validación"""
    pass


class Validator:
    """Validador centralizado para la aplicación"""
    
    @staticmethod
    def is_valid_amount(value: Any) -> bool:
        """Valida que un valor sea un monto válido"""
        try:
            amount = float(value)
            return amount >= 0 and amount <= 999999999
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_category(category: str) -> bool:
        """Valida que una categoría sea válida"""
        if not isinstance(category, str):
            return False
        return 3 <= len(category) <= 50 and category.isalnum() or ' ' in category
    
    @staticmethod
    def is_valid_description(description: str) -> bool:
        """Valida descripción"""
        if not isinstance(description, str):
            return False
        return 0 <= len(description) <= 255
    
    @staticmethod
    def is_valid_date(date_obj: Any) -> bool:
        """Valida que sea una fecha válida"""
        try:
            if isinstance(date_obj, datetime):
                return True
            if isinstance(date_obj, str):
                datetime.fromisoformat(date_obj)
                return True
            return False
        except:
            return False
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return isinstance(email, str) and re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_currency(value: str) -> bool:
        """Valida formato de moneda"""
        pattern = r'^[\$\€\¥]?\s?\d+[.,]\d{2}$'
        return isinstance(value, str) and re.match(pattern, value) is not None
    
    @staticmethod
    def validate_gasto(data: Dict) -> Union[bool, str]:
        """Valida estructura completa de un gasto"""
        required_fields = ['monto', 'categoria', 'fecha']
        
        for field in required_fields:
            if field not in data:
                return f"Falta el campo: {field}"
        
        if not Validator.is_valid_amount(data['monto']):
            return "Monto inválido"
        
        if not Validator.is_valid_category(data['categoria']):
            return "Categoría inválida"
        
        if not Validator.is_valid_date(data['fecha']):
            return "Fecha inválida"
        
        return True
    
    @staticmethod
    def validate_ingreso(data: Dict) -> Union[bool, str]:
        """Valida estructura completa de un ingreso"""
        required_fields = ['monto', 'fuente', 'fecha']
        
        for field in required_fields:
            if field not in data:
                return f"Falta el campo: {field}"
        
        if not Validator.is_valid_amount(data['monto']):
            return "Monto inválido"
        
        if not Validator.is_valid_category(data['fuente']):
            return "Fuente inválida"
        
        if not Validator.is_valid_date(data['fecha']):
            return "Fecha inválida"
        
        return True
    
    @staticmethod
    def sanitize_input(value: str, max_length: int = 255) -> str:
        """Sanitiza entrada de usuario"""
        if not isinstance(value, str):
            return ""
        return value.strip()[:max_length]
