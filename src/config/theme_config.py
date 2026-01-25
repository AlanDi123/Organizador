# src/config/theme_config.py
"""
Sistema moderno de temas para la aplicación.
Soporta múltiples esquemas de color y personalización.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ColorScheme:
    """Esquema de colores con validación"""
    fondo: str
    panel: str
    texto: str
    acento: str
    destacado: str
    alerta: str
    exito: str
    borde: str
    
    def validate(self) -> bool:
        """Valida que todos los colores sean hexadecimales válidos"""
        colors = [
            self.fondo, self.panel, self.texto, self.acento,
            self.destacado, self.alerta, self.exito, self.borde
        ]
        for color in colors:
            if not isinstance(color, str) or not color.startswith('#'):
                return False
        return True


class ThemeManager:
    """Gestor centralizado de temas con soporte para múltiples esquemas"""
    
    LIGHT_THEME = ColorScheme(
        fondo="#fff0f5",
        panel="#ffffff",
        texto="#000000",
        acento="#8b008b",
        destacado="#ff69b4",
        alerta="#ff4500",
        exito="#228b22",
        borde="#dda0dd"
    )
    
    DARK_THEME = ColorScheme(
        fondo="#1a1a2e",
        panel="#16213e",
        texto="#eaeaea",
        acento="#00d4ff",
        destacado="#00a8cc",
        alerta="#ff6b6b",
        exito="#51cf66",
        borde="#0f3460"
    )
    
    OCEAN_THEME = ColorScheme(
        fondo="#e0f7ff",
        panel="#ffffff",
        texto="#003d5c",
        acento="#0099cc",
        destacado="#00ccff",
        alerta="#ff6b35",
        exito="#004e89",
        borde="#cce7ff"
    )
    
    FOREST_THEME = ColorScheme(
        fondo="#f5faf7",
        panel="#ffffff",
        texto="#1b3a24",
        acento="#2d6a4f",
        destacado="#52b788",
        alerta="#d62828",
        exito="#74c69d",
        borde="#b7e4c7"
    )
    
    THEMES: Dict[str, ColorScheme] = {
        'light': LIGHT_THEME,
        'dark': DARK_THEME,
        'ocean': OCEAN_THEME,
        'forest': FOREST_THEME,
    }
    
    @classmethod
    def get_theme(cls, name: str) -> Optional[ColorScheme]:
        """Obtiene un tema por nombre"""
        return cls.THEMES.get(name.lower())
    
    @classmethod
    def list_themes(cls) -> list:
        """Lista todos los temas disponibles"""
        return list(cls.THEMES.keys())
    
    @classmethod
    def validate_all_themes(cls) -> bool:
        """Valida todos los temas"""
        for theme in cls.THEMES.values():
            if not theme.validate():
                return False
        return True


class FontConfig:
    """Configuración centralizada de fuentes"""
    
    FONT_PRIMARY = ("Segoe UI", 10)
    FONT_TITLE = ("Segoe UI", 14, "bold")
    FONT_SUBTITLE = ("Segoe UI", 12, "bold")
    FONT_SMALL = ("Segoe UI", 9)
    FONT_MONO = ("Courier New", 9)
    
    # Para sistemas sin Segoe UI (Linux)
    FALLBACK_FONTS = [
        ("Ubuntu", 10),
        ("DejaVu Sans", 10),
        ("Liberation Sans", 10),
        ("Arial", 10),
    ]


class AppConfig:
    """Configuración global de la aplicación"""
    
    # Ventana
    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    WINDOW_MIN_WIDTH = 800
    WINDOW_MIN_HEIGHT = 600
    
    # Base de datos
    DB_PATH = "data/finanzas.db"
    BACKUP_PATH = "data/backups"
    
    # Presupuesto
    DEFAULT_BUDGET_FILE = "presupuesto_ia.json"
    BUDGET_HISTORY_DAYS = 30
    
    # Performance
    MAX_CACHE_SIZE = 100
    CACHE_TTL = 3600  # 1 hora
    
    # UI
    DEFAULT_THEME = 'light'
    ANIMATION_SPEED = 200  # ms
    REFRESH_RATE = 1000  # ms
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "logs/app.log"
    
    # Features
    ENABLE_AI_FEATURES = True
    ENABLE_DARK_MODE = True
    ENABLE_EXPORT = True
    ENABLE_IMPORT = True
    ENABLE_BACKUP = True
