# GUÍA DE TYPE HINTS Y VALIDACIÓN

## 📝 Convenciones de Type Hints

La aplicación ahora usa type hints en todo el código. Esto ayuda a:
- Detectar errores en tiempo de desarrollo
- Mejorar la inteligencia de IDEs
- Documentar automáticamente el código

### Ejemplos:

```python
from typing import List, Dict, Optional, Tuple, Any

# Funciones básicas
def cargar_datos(tabla: str) -> List[Dict[str, Any]]:
    """Carga datos de una tabla"""
    pass

# Funciones con valores opcionales
def obtener_usuario(id: int, incluir_historial: bool = False) -> Optional[Dict]:
    """Obtiene un usuario por ID"""
    pass

# Funciones complejas
def procesar_gastos(gastos: List[Dict]) -> Tuple[float, List[str]]:
    """Procesa gastos y retorna (total, categorías)"""
    pass
```

## ✅ Sistema de Validación Automática

### 1. Validación con decorador @validate_types

```python
from src.utils.decorators import validate_types

@validate_types(monto=float, categoria=str)
def agregar_gasto(monto: float, categoria: str) -> bool:
    """Automáticamente valida tipos"""
    pass
```

### 2. Validación con Validator

```python
from src.utils.validators import Validator

# Validar monto
if Validator.is_valid_amount(100):
    print("✅ Monto válido")

# Validar estructura completa
result = Validator.validate_gasto({
    'monto': 100,
    'categoria': 'food',
    'fecha': '2024-01-01'
})

if result == True:
    print("✅ Gasto válido")
else:
    print(f"❌ Error: {result}")
```

## 🔄 Migraciones Automáticas

Las migraciones se ejecutan automáticamente en el startup:

```python
from src.utils.db_migration import run_migrations, validate_database

# Las migraciones se ejecutan automáticamente
# Pero puedes hacerlo manualmente:
if run_migrations():
    print("✅ Migraciones completadas")

# Validar integridad
if validate_database():
    print("✅ Base de datos íntegra")
```

## 🚀 Inicialización Automática

El archivo `run.py` ahora ejecuta inicialización automática:

```
📂 Directorio raíz configurado
🐧 Configuración de Linux aplicada
🔧 INICIALIZANDO SISTEMA...
  ✅ Logging
  ✅ Directorios
  ✅ Base de datos
  ✅ Caché
  ✅ Eventos
✅ SISTEMA LISTO - INICIANDO UI...
```

## 📊 Decoradores Disponibles

### @timer
Mide el tiempo de ejecución:
```python
@timer
def funcion_lenta():
    time.sleep(1)
# Output: funcion_lenta tomó 1.001s
```

### @retry
Reintenta en caso de error:
```python
@retry(max_attempts=3, delay=1.0)
def conectar_api():
    # Reintenta hasta 3 veces
    pass
```

### @safe_execute
Ejecuta función de forma segura:
```python
@safe_execute(default_return=[])
def obtener_datos():
    # Si falla, retorna []
    pass
```

### @cacheable
Cachea resultados automáticamente:
```python
@cacheable(ttl=3600)  # Cachea por 1 hora
def calcular_total():
    return sum(...)
```

## 🔧 Variables de Entorno

Configurables en `.env`:

```
DEBUG=False
LOG_LEVEL=INFO
CACHE_TTL=3600
ENABLE_AI=True
```

Cargadas automáticamente en `src/config/env_config.py`

## 📋 Checklist de Calidad

- ✅ Type hints en todas las funciones
- ✅ Validación automática de entrada
- ✅ Logging centralizado
- ✅ Tests básicos con pytest
- ✅ Decoradores para funcionalidades comunes
- ✅ Manejo de excepciones personalizado
- ✅ Migraciones automáticas de BD
- ✅ Caché inteligente con TTL
- ✅ Bus de eventos desacoplado
- ✅ Configuración desde variables de entorno
