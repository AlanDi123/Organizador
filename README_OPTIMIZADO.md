# 💰 Organizador de Gastos e Ingresos - Versión Optimizada

**Aplicación ligera y compatible para sistemas con pocos recursos (1GB RAM, procesadores antiguos)**

## ✨ Características Principales

- ✅ **Muy Ligera**: Sin NumPy, sin CustomTkinter. Solo ~50MB de dependencias
- ✅ **Compatible**: Funciona en Linux, Windows y macOS
- ✅ **Hardware Antiguo**: Optimizada para sistemas con 1GB RAM o menos
- ✅ **Multiplataforma**: Same code, todos los sistemas operativos
- ✅ **Gestor de Gastos**: Registra ingresos y gastos con categorización
- ✅ **Análisis Inteligente**: Detección de anomalías y recomendaciones
- ✅ **Base de Datos Local**: SQLite - no requiere internet para funcionar

## 📋 Requisitos Mínimos

- **Python**: 3.9 o superior
- **RAM**: 512MB - 1GB
- **Almacenamiento**: 100MB
- **Sistema**: Linux Mint, Ubuntu, Debian, Windows 7+, macOS 10.12+

## 🚀 Instalación Rápida

### Linux (Linux Mint, Ubuntu, Debian)

```bash
# 1. Clonar o descargar el proyecto
cd organizador

# 2. Ejecutar instalador
chmod +x install.sh
./install.sh

# 3. Ejecutar la aplicación
./run.sh
```

### Windows

```bash
# 1. Abrir CMD o PowerShell en la carpeta del proyecto
cd organizador

# 2. Ejecutar el script de ejecución
run.bat
```

### macOS

```bash
# 1. Ir a la carpeta del proyecto
cd organizador

# 2. Ejecutar instalador
chmod +x install.sh
./install.sh

# 3. Ejecutar la aplicación
./run.sh
```

## 🔧 Instalación Manual (si los scripts no funcionan)

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
# En Linux/macOS:
source venv/bin/activate
# En Windows:
venv\Scripts\activate.bat

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python3 start_app.py
```

## 📁 Estructura del Proyecto

```
organizador/
├── src/
│   ├── models/           # Modelos de datos (gastos, ingresos, IA)
│   ├── views/            # Interfaz gráfica (Tkinter)
│   ├── controllers/       # Controladores de lógica
│   └── utils/            # Utilidades (BD, math, etc)
├── data/                 # Datos de la aplicación (BD SQLite)
├── assets/               # Imágenes y recursos
├── requirements.txt      # Dependencias Python
├── start_app.py         # Script de inicio principal
├── run.sh               # Script de ejecución (Linux/macOS)
├── run.bat              # Script de ejecución (Windows)
└── install.sh           # Script de instalación (Linux/macOS)
```

## 🎯 Características por Módulo

### 📊 Gestión de Gastos e Ingresos
- Registra gastos e ingresos con categorización automática
- Soporte para gastos recurrentes
- Historial completo con búsqueda

### 🤖 Módulo de IA
- Categorización automática basada en palabras clave
- Detección de gastos anómalos (z-score)
- Recomendaciones financieras personalizadas
- Análisis de tendencias

### 💼 Presupuesto Inteligente
- Establecer presupuestos por categoría
- Comparar presupuestado vs. gastado
- Alertas cuando se acerca al límite

### 📈 Dashboard Financiero
- Vista general de ingresos y gastos
- Gráficos por categoría
- Estadísticas mensuales

## ⚙️ Configuración

### Archivo de configuración: `data/ia_config.json`

```json
{
  "categorias_gasto": {
    "alimentación": [...],
    "transporte": [...],
    // ...más categorías
  },
  "anomalias": {
    "umbral_z": 2.0
  },
  "recomendaciones": {
    "umbral_ahorro_bajo": 10,
    "umbral_ahorro_optimo": 20
  }
}
```

## 🆘 Solución de Problemas

### Error: "Python not found"
**Solución**: Instalar Python desde https://www.python.org/

En Linux:
```bash
# Debian/Ubuntu
sudo apt install python3 python3-pip python3-venv

# Linux Mint (generalmente ya está instalado)
python3 --version
```

### Error: "No module named 'src'"
**Solución**: Asegúrate de estar en la carpeta raíz del proyecto y que `start_app.py` está allí.

```bash
pwd  # Verificar que estás en /ruta/a/organizador
ls src/  # Debe mostrar carpetas (controllers, models, views, utils)
```

### Aplicación muy lenta
**Soluciones**:
1. Cerrar otras aplicaciones para liberar RAM
2. Limpiar la base de datos: eliminar archivos muy antiguos
3. Usar el "Modo Oscuro" que consume menos recursos gráficos

### Error de permisos en Linux
```bash
chmod +x run.sh install.sh
```

## 🔐 Seguridad

- ✅ Base de datos local (sin conexiones remotas)
- ✅ Sin envío de datos a servidores externos (excepto OpenAI API si se configura)
- ✅ Contraseña opcional para la aplicación
- ✅ Backups automáticos de datos

## 📦 Dependencias Instaladas

| Paquete | Versión | Propósito | Tamaño |
|---------|---------|----------|--------|
| Pillow | 10.0.0 | Procesamiento de imágenes | ~8MB |
| Matplotlib | 3.8.0 | Gráficos | ~15MB |
| Requests | 2.31.0 | HTTP requests | ~3MB |
| tkcalendar | 1.6.1 | Widget de calendario | ~1MB |
| OpenAI | 1.3.5 | API OpenAI (opcional) | ~3MB |

**Total**: ~50MB (muy ligero)

## 💡 Consejos de Optimización

Para sistemas muy antiguos (512MB RAM):

1. **Desactiva animaciones gráficas**: Edita `main_app.py` y comenta gráficos 3D
2. **Usa modo oscuro**: Consume menos recursos que modo claro
3. **Limpia la BD regularmente**: `data/finanzas.db` puede crecer
4. **Cierra otras aplicaciones**: Navegadores web, Discord, etc.

## 📝 Licencia

MIT License - Libre para uso personal y comercial

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para reportar bugs o sugerir mejoras:
1. Abre un issue
2. Fork el proyecto
3. Crea una rama para tu feature
4. Envía un pull request

## 📧 Contacto

Para soporte o consultas: [añadir email o contacto]

---

**¡Disfruta de tu Organizador Financiero Optimizado! 💰**
