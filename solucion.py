import os
import sqlite3
from datetime import datetime

# Eliminar el archivo de respaldo corrupto
if os.path.exists('finanzas_historial_backup.json'):
    os.remove('finanzas_historial_backup.json')
    print("Archivo de respaldo corrupto eliminado.")

# Conexión a la base de datos
conn = sqlite3.connect('finanzas.db')
cursor = conn.cursor()

# Verificar y crear columnas es_historial
try:
    cursor.execute("SELECT es_historial FROM gastos LIMIT 1")
except sqlite3.OperationalError:
    print("Añadiendo la columna es_historial a la tabla gastos")
    cursor.execute("ALTER TABLE gastos ADD COLUMN es_historial BOOLEAN DEFAULT 0")

try:
    cursor.execute("SELECT es_historial FROM ingresos LIMIT 1")
except sqlite3.OperationalError:
    print("Añadiendo la columna es_historial a la tabla ingresos")
    cursor.execute("ALTER TABLE ingresos ADD COLUMN es_historial BOOLEAN DEFAULT 0")

# Crear entradas de historial directamente a partir de los datos existentes
print("Creando registros de historial para gastos...")
fecha_actual = datetime.now().strftime("%Y-%m-%d")

# Borrar entradas de historial existentes para evitar duplicados
try:
    cursor.execute("DELETE FROM gastos WHERE es_historial = 1")
    cursor.execute("DELETE FROM ingresos WHERE es_historial = 1")
    print("Entradas de historial existentes eliminadas.")
except:
    pass

# Crear nuevas entradas de historial para gastos
cursor.execute("SELECT DISTINCT nombre, MAX(recurrente) FROM gastos GROUP BY nombre")
gastos = cursor.fetchall()
for nombre, recurrente in gastos:
    if nombre and nombre.strip():
        cursor.execute(
            'INSERT INTO gastos (nombre, monto, recurrente, fecha, es_historial) VALUES (?, ?, ?, ?, ?)',
            (nombre, 0, recurrente, fecha_actual, 1)
        )
print(f"Se crearon {len(gastos)} entradas de historial para gastos.")

# Crear nuevas entradas de historial para ingresos
cursor.execute("SELECT DISTINCT concepto FROM ingresos")
conceptos = cursor.fetchall()
for (concepto,) in conceptos:
    if concepto and concepto.strip():
        cursor.execute(
            'INSERT INTO ingresos (concepto, monto, fecha, es_historial) VALUES (?, ?, ?, ?)',
            (concepto, 0, fecha_actual, 1)
        )
print(f"Se crearon {len(conceptos)} entradas de historial para ingresos.")

# Crear índices para mejorar rendimiento
try:
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gastos_historial ON gastos(es_historial)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingresos_historial ON ingresos(es_historial)')
    print("Índices creados correctamente")
except Exception as e:
    print(f"Error al crear índices: {e}")

# Guardar cambios
conn.commit()
conn.close()

print("¡Reparación completada! Ahora puedes ejecutar la aplicación normalmente.")