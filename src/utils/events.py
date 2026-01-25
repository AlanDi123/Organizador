# src/utils/events.py
"""
Sistema de eventos para desacoplamiento de componentes.
"""

from typing import Callable, Dict, List, Any
from dataclasses import dataclass


@dataclass
class Event:
    """Clase base para eventos"""
    name: str
    data: Any = None
    timestamp: float = None
    
    def __post_init__(self):
        import time
        if self.timestamp is None:
            self.timestamp = time.time()


class EventBus:
    """Bus de eventos para comunicación entre componentes"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa el bus de eventos"""
        self.listeners: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history = 100
    
    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Se suscribe a un evento"""
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)
    
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """Se desuscribe de un evento"""
        if event_name in self.listeners:
            self.listeners[event_name] = [
                cb for cb in self.listeners[event_name] if cb != callback
            ]
    
    def publish(self, event: Event) -> None:
        """Publica un evento"""
        # Guardar en historial
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Notificar listeners
        if event.name in self.listeners:
            for callback in self.listeners[event.name]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error en listener para {event.name}: {e}")
    
    def clear_listeners(self, event_name: str = None) -> None:
        """Limpia listeners"""
        if event_name:
            self.listeners.pop(event_name, None)
        else:
            self.listeners.clear()


# Eventos estándar de la aplicación
class AppEvents:
    THEME_CHANGED = "theme_changed"
    DATA_UPDATED = "data_updated"
    GASTO_ADDED = "gasto_added"
    GASTO_DELETED = "gasto_deleted"
    GASTO_UPDATED = "gasto_updated"
    INGRESO_ADDED = "ingreso_added"
    INGRESO_DELETED = "ingreso_deleted"
    INGRESO_UPDATED = "ingreso_updated"
    PRESUPUESTO_UPDATED = "presupuesto_updated"
    ERROR_OCCURRED = "error_occurred"
    SUCCESS = "success"


def get_event_bus() -> EventBus:
    """Obtiene la instancia global del bus de eventos"""
    return EventBus()
