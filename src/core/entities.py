"""
Entidades de negocio compartidas
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Gasto:
    """Entidad de Gasto"""
    nombre: str
    monto: float
    recurrente: bool = False
    fecha: str = ""
    categoria: str = "otros"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_creacion: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nombre': self.nombre,
            'monto': self.monto,
            'recurrente': self.recurrente,
            'fecha': self.fecha or datetime.now().strftime("%Y-%m-%d"),
            'categoria': self.categoria,
            'fecha_creacion': self.fecha_creacion
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Gasto':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            nombre=data.get('nombre', ''),
            monto=data.get('monto', 0.0),
            recurrente=data.get('recurrente', False),
            fecha=data.get('fecha', ''),
            categoria=data.get('categoria', 'otros'),
            fecha_creacion=data.get('fecha_creacion', '')
        )


@dataclass
class Ingreso:
    """Entidad de Ingreso"""
    concepto: str
    monto: float
    fecha: str = ""
    categoria: str = "otros"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_creacion: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'concepto': self.concepto,
            'monto': self.monto,
            'fecha': self.fecha or datetime.now().strftime("%Y-%m-%d"),
            'categoria': self.categoria,
            'fecha_creacion': self.fecha_creacion
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Ingreso':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            concepto=data.get('concepto', ''),
            monto=data.get('monto', 0.0),
            fecha=data.get('fecha', ''),
            categoria=data.get('categoria', 'otros'),
            fecha_creacion=data.get('fecha_creacion', '')
        )


@dataclass
class Categoria:
    """Categoría para clasificación de gastos/ingresos"""
    nombre: str
    color: str = "#FF69B4"
    icono: str = "📊"
    presupuesto_maximo: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'nombre': self.nombre,
            'color': self.color,
            'icono': self.icono,
            'presupuesto_maximo': self.presupuesto_maximo
        }


@dataclass
class Presupuesto:
    """Presupuesto mensual por categoría"""
    mes: int
    anio: int
    categorias: dict = field(default_factory=dict)
    total_presupuestado: float = 0.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'mes': self.mes,
            'anio': self.anio,
            'categorias': self.categorias,
            'total_presupuestado': self.total_presupuestado
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Presupuesto':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            mes=data.get('mes', datetime.now().month),
            anio=data.get('anio', datetime.now().year),
            categorias=data.get('categorias', {}),
            total_presupuestado=data.get('total_presupuestado', 0.0)
        )
