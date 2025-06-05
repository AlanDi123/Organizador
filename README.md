# Organizador de Gastos e Ingresos

## Descripción
Esta aplicación de escritorio permite gestionar gastos e ingresos personales, con funcionalidades para registrar, visualizar y analizar movimientos financieros.

## Nuevas Características
- **Fecha de publicación quincenal para gastos**: La aplicación calcula automáticamente la fecha de la próxima quincena (día 15 o 1 del siguiente mes) para los gastos.
- **Fecha de ingresos quincenal a semana vencida**: Se calcula la fecha de ingreso como una semana después de la quincena.
- **Historial de conceptos de ingresos**: Se mantiene un registro histórico de los conceptos de ingresos, permitiendo su reutilización y análisis estadístico.
- **Función "Borrar Todo"**: Ahora es posible borrar todos los datos de la aplicación con un solo botón.
- **Código reestructurado**: La aplicación ha sido reorganizada siguiendo un patrón MVC (Modelo-Vista-Controlador) para mejorar la mantenibilidad.

## Estructura del Proyecto
```
organizador_finanzas/
├── main.py                  # Punto de entrada principal
├── utils.py                 # Funciones de utilidad
├── model/
│   ├── data_manager.py      # Gestor de datos para la base de datos
│   ├── gastos.py            # Lógica de negocio para gastos
│   └── ingresos.py          # Lógica de negocio para ingresos
└── ui/
    ├── app_controller.py    # Controlador principal de la UI
    └── frames/
        ├── gastos_frame.py  # Frame para gestión de gastos
        └── ingresos_frame.py # Frame para gestión de ingresos
```

## Cómo Usar
1. Ejecute `main.py` para iniciar la aplicación.
2. Para agregar un gasto:
   - Ingrese el nombre y monto del gasto
   - La fecha de la próxima quincena se calcula automáticamente
   - Marque si es recurrente
   - Haga clic en "Agregar Gasto"

3. Para agregar un ingreso:
   - Seleccione o ingrese un concepto (puede elegir del historial)
   - Ingrese el monto
   - La fecha (una semana después de la quincena) se calcula automáticamente
   - Haga clic en "Agregar Ingreso"

4. Funciones adicionales:
   - Consultar el historial de conceptos de ingresos
   - Ver balance general
   - Borrar todos los datos (con confirmación)
   - Modo noche/día para la interfaz

## Requisitos
- Python 3.6 o superior
- Bibliotecas: tkinter, PIL (Pillow), requests, sqlite3 (incluido en Python)

## Instalación
1. Clone o descargue este repositorio
2. Instale las dependencias desde `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecute la aplicación:
   ```
   python main.py
   ```

### Uso desde la línea de comandos
Puede utilizar `cli.py` para obtener un resumen rápido de los totales:
```bash
python cli.py --totales
```

## Versión Android (experimental)
Se incluye `kivy_main.py`, una interfaz simplificada basada en Kivy para
dispositivos móviles. Para generar un APK utilice
[Buildozer](https://github.com/kivy/buildozer) en un entorno Linux:

```bash
pip install buildozer
buildozer -v android debug
```

El archivo `buildozer.spec` está preconfigurado y el APK generado se
encontrará en el directorio `bin/`.

### Compilación desde Windows 10
Buildozer requiere un entorno Linux. En Windows 10 Pro la forma más sencilla de
usar Buildozer es instalar [WSL2](https://learn.microsoft.com/windows/wsl/)
(Ubuntu recomendado) y ejecutar desde allí los comandos anteriores:

```bash
wsl
cd ruta/a/este/repositorio
pip install buildozer
buildozer -v android debug
```

También se puede usar una máquina virtual Linux (por ejemplo VirtualBox) si se
prefiere no usar WSL.

## Notas
- La aplicación creará automáticamente una base de datos SQLite (`finanzas.db`) en el directorio de ejecución.
- Si actualiza desde una versión anterior, la base de datos se migrará automáticamente para incluir los nuevos campos.
- Puede ejecutar las pruebas unitarias con:
   ```bash
   pytest
   ```
