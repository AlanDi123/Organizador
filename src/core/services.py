"""
Servicios de negocio - Lógica compartida desktop/móvil
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.core.entities import Gasto, Ingreso, Presupuesto, Categoria
from src.models.data_manager import (
    cargar_datos,
    guardar_gasto,
    guardar_ingreso,
    eliminar_dato,
    cargar_historial_gastos,
    cargar_historial_conceptos,
    DBConnectionManager
)
from src.cloud.firebase_client import FirebaseClient
from src.cloud.sync_engine import SyncEngine

logger = logging.getLogger(__name__)


class GastosService:
    """Servicio para gestión de gastos"""
    
    @staticmethod
    def obtener_todos() -> List[Gasto]:
        """Obtiene todos los gastos"""
        datos = cargar_datos('gastos')
        return [Gasto(
            id=str(g[0]),
            nombre=g[1],
            monto=g[2],
            recurrente=bool(g[3]) if len(g) > 3 and g[3] else False,
            fecha=g[4] if len(g) > 4 and g[4] else "",
            fecha_creacion=g[6] if len(g) > 6 and g[6] else ""
        ) for g in datos if g[2] > 0]  # Filtrar historial (monto = 0)
    
    @staticmethod
    def obtener_por_id(gasto_id: int) -> Optional[Gasto]:
        """Obtiene un gasto por ID"""
        gastos = GastosService.obtener_todos()
        for g in gastos:
            if g.id == str(gasto_id):
                return g
        return None
    
    @staticmethod
    def crear(nombre: str, monto: float, recurrente: bool = False, 
              fecha: str = None, categoria: str = "otros") -> bool:
        """Crea un nuevo gasto"""
        if fecha is None:
            fecha = datetime.now().strftime("%Y-%m-%d")
        
        exito = guardar_gasto(nombre, monto, recurrente, fecha)
        
        if exito:
            # Trigger sync si está disponible
            try:
                sync = SyncEngine()
                if sync.firebase.enabled:
                    sync.force_sync()
            except:
                pass
        
        return exito
    
    @staticmethod
    def eliminar(gasto_id: int) -> bool:
        """Elimina un gasto"""
        return eliminar_dato('gastos', 'id', gasto_id)
    
    @staticmethod
    def obtener_historial_nombres() -> List[str]:
        """Obtiene nombres históricos para autocompletado"""
        return cargar_historial_gastos() or []
    
    @staticmethod
    def calcular_total() -> float:
        """Calcula el total de gastos"""
        gastos = GastosService.obtener_todos()
        return sum(g.monto for g in gastos)
    
    @staticmethod
    def obtener_por_fecha(fecha_inicio: str, fecha_fin: str) -> List[Gasto]:
        """Obtiene gastos en un rango de fechas"""
        todos = GastosService.obtener_todos()
        return [g for g in todos if fecha_inicio <= g.fecha <= fecha_fin]


class IngresosService:
    """Servicio para gestión de ingresos"""
    
    @staticmethod
    def obtener_todos() -> List[Ingreso]:
        """Obtiene todos los ingresos"""
        datos = cargar_datos('ingresos')
        return [Ingreso(
            id=str(i[0]),
            concepto=i[1],
            monto=i[2],
            fecha=i[3] if len(i) > 3 and i[3] else "",
            fecha_creacion=i[5] if len(i) > 5 and i[5] else ""
        ) for i in datos if i[2] > 0]  # Filtrar historial
    
    @staticmethod
    def obtener_por_id(ingreso_id: int) -> Optional[Ingreso]:
        """Obtiene un ingreso por ID"""
        ingresos = IngresosService.obtener_todos()
        for i in ingresos:
            if i.id == str(ingreso_id):
                return i
        return None
    
    @staticmethod
    def crear(concepto: str, monto: float, fecha: str = None, 
              categoria: str = "otros") -> bool:
        """Crea un nuevo ingreso"""
        if fecha is None:
            fecha = datetime.now().strftime("%Y-%m-%d")
        
        exito = guardar_ingreso(concepto, monto, fecha)
        
        if exito:
            # Trigger sync
            try:
                sync = SyncEngine()
                if sync.firebase.enabled:
                    sync.force_sync()
            except:
                pass
        
        return exito
    
    @staticmethod
    def eliminar(ingreso_id: int) -> bool:
        """Elimina un ingreso"""
        return eliminar_dato('ingresos', 'id', ingreso_id)
    
    @staticmethod
    def obtener_historial_conceptos() -> List[str]:
        """Obtiene conceptos históricos para autocompletado"""
        return cargar_historial_conceptos() or []
    
    @staticmethod
    def calcular_total() -> float:
        """Calcula el total de ingresos"""
        ingresos = IngresosService.obtener_todos()
        return sum(i.monto for i in ingresos)


class PresupuestoService:
    """Servicio para gestión de presupuestos"""
    
    def __init__(self):
        from src.models.presupuesto_ia import PresupuestoInteligente
        self.sistema = PresupuestoInteligente()
    
    def generar_presupuesto_sugerido(self, mes: int = None, anio: int = None) -> Presupuesto:
        """Genera presupuesto sugerido basado en historial"""
        if mes is None:
            mes = datetime.now().month
        if anio is None:
            anio = datetime.now().year
        
        presupuesto_data = self.sistema.generar_presupuesto_sugerido()
        
        return Presupuesto(
            mes=mes,
            anio=anio,
            categorias=presupuesto_data.get('categorias', {}),
            total_presupuestado=presupuesto_data.get('total', 0.0)
        )
    
    def obtener_presupuesto_actual(self) -> Optional[Presupuesto]:
        """Obtiene presupuesto actual guardado"""
        presupuesto_data = self.sistema.cargar_presupuesto_actual()
        
        if not presupuesto_data:
            return None
        
        return Presupuesto.from_dict(presupuesto_data)
    
    def guardar_presupuesto(self, presupuesto: Presupuesto) -> bool:
        """Guarda presupuesto"""
        try:
            self.sistema.guardar_presupuesto(presupuesto.to_dict())
            return True
        except Exception as e:
            logger.error(f"Error al guardar presupuesto: {e}")
            return False


class AuthService:
    """Servicio para autenticación y gestión de usuarios"""
    
    def __init__(self):
        self.firebase = FirebaseClient()
    
    def registrar(self, email: str, password: str, display_name: str = "") -> bool:
        """Registra nuevo usuario"""
        user_id = self.firebase.create_user(email, password, display_name)
        return user_id is not None
    
    def login(self, email: str, password: str) -> bool:
        """Inicia sesión"""
        user_id = self.firebase.authenticate(email, password)
        return user_id is not None
    
    def logout(self):
        """Cierra sesión"""
        self.firebase.sign_out()
    
    def esta_autenticado(self) -> bool:
        """Verifica si hay usuario autenticado"""
        return self.firebase.is_authenticated()
    
    def obtener_user_id(self) -> Optional[str]:
        """Obtiene ID del usuario"""
        return self.firebase.get_user_id()
    
    def sincronizar_datos(self) -> Dict[str, int]:
        """Ejecuta sincronización de datos"""
        sync = SyncEngine()
        return sync.sync_all()
    
    def obtener_estado_sync(self) -> Dict[str, Any]:
        """Obtiene estado de sincronización"""
        sync = SyncEngine()
        return sync.get_sync_status()
