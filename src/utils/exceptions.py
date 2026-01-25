# src/utils/exceptions.py
"""
Excepciones personalizadas para la aplicación.
"""


class AppException(Exception):
    """Excepción base de la aplicación"""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            "message": self.message,
            "code": self.code,
            "details": self.details
        }


class ValidationError(AppException):
    """Error de validación de datos"""
    
    def __init__(self, message: str, field: str = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field})


class DatabaseError(AppException):
    """Error en operaciones de base de datos"""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(message, "DATABASE_ERROR", {"operation": operation})


class ConfigError(AppException):
    """Error de configuración"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIG_ERROR", {"config_key": config_key})


class AIError(AppException):
    """Error en módulo de IA"""
    
    def __init__(self, message: str, ai_operation: str = None):
        super().__init__(message, "AI_ERROR", {"operation": ai_operation})


class FileOperationError(AppException):
    """Error en operaciones de archivo"""
    
    def __init__(self, message: str, filename: str = None, operation: str = None):
        super().__init__(
            message,
            "FILE_OPERATION_ERROR",
            {"filename": filename, "operation": operation}
        )
