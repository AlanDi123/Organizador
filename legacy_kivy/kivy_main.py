# -*- coding: utf-8 -*-
"""
kivy_main.py - Aplicación Kivy monolítica que integra toda la funcionalidad
del Organizador de Gastos e Ingresos (versión para APK).
Incluye la lógica de acceso a la base de datos SQLite, cálculo de totales,
categorías IA básicas, y toda la interfaz en una sola pieza.
"""

import os
import sqlite3
from datetime import datetime, timedelta
import threading
import requests

from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

# --- PARTE I: Lógica de datos (data_manager) ---

DB_FILENAME = "finanzas.db"

def obtener_conexion():
    """
    Crea la carpeta local si no existe y abre/crea la base de datos SQLite.
    Retorna un objeto sqlite3.Connection.
    """
    # Asegurarse de crear el archivo en la carpeta de la aplicación
    basedir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(basedir, DB_FILENAME)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn

# Inicializar la base de datos y tablas si no existen
def inicializar_bd():
    conn = obtener_conexion()
    cursor = conn.cursor()
    # Tabla de gastos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            monto REAL NOT NULL,
            recurrente INTEGER NOT NULL DEFAULT 0,
            fecha TEXT
        );
    """)
    # Tabla de ingresos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT,
            es_historial INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.commit()
    conn.close()

# Llamar al inicio
inicializar_bd()

def guardar_gasto(nombre, monto, recurrente=False, fecha=None):
    """
    Inserta un nuevo gasto en la tabla 'gastos'. Fecha en formato 'YYYY-MM-DD' o None.
    Retorna True si tuvo éxito, False en caso de error.
    """
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        rec_flag = 1 if recurrente else 0
        # Si no se provee fecha, calcular la próxima quincena:
        if not fecha:
            fecha = calcular_fecha_proxima_quincena()
        cursor.execute(
            "INSERT INTO gastos (nombre, monto, recurrente, fecha) VALUES (?, ?, ?, ?);",
            (nombre, monto, rec_flag, fecha)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al guardar gasto:", e)
        return False

def calcular_fecha_proxima_quincena():
    """
    Según lógica original: si estamos antes o el día 15 o 1, asigna esa fecha;
    si ya pasó, avanza a la próxima quincena:
    - Si día actual <= 15, fijar día 15 del mes actual.
    - Si día actual > 15, fijar día 1 del mes siguiente.
    Retorna cadena 'YYYY-MM-DD'.
    """
    hoy = datetime.now().date()
    if hoy.day <= 15:
        fecha = hoy.replace(day=15)
    else:
        # Siguiente mes, día 1
        year = hoy.year + (1 if hoy.month == 12 else 0)
        month = 1 if hoy.month == 12 else hoy.month + 1
        fecha = hoy.replace(year=year, month=month, day=1)
    return fecha.isoformat()

def guardar_ingreso(concepto, monto, fecha=None):
    """
    Inserta un nuevo ingreso en la tabla 'ingresos'. Si fecha es None,
    calcular fecha de ingreso: una semana después de la quincena actual.
    Retorna True si tuvo éxito.
    """
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        # Fecha ingreso: semana después de la quincena más reciente
        if not fecha:
            fecha = calcular_fecha_ingreso_semana_vencida()
        # Insertar. es_historial=0 para ingreso real.
        cursor.execute(
            "INSERT INTO ingresos (concepto, monto, fecha, es_historial) VALUES (?, ?, ?, 0);",
            (concepto, monto, fecha)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al guardar ingreso:", e)
        return False

def calcular_fecha_ingreso_semana_vencida():
    """
    Calcula la fecha de ingreso: toma la quincena (día 15 o 1) más reciente
    y le suma 7 días.
    """
    hoy = datetime.now().date()
    if hoy.day <= 15:
        # Quincena de día 1 del mes actual
        base = hoy.replace(day=1)
    else:
        # Quincena de día 15 del mes actual
        base = hoy.replace(day=15)
    ingreso_fecha = base + timedelta(days=7)
    return ingreso_fecha.isoformat()

def cargar_datos(tipo, incluir_historial=False):
    """
    Retorna lista de registros de la tabla 'gastos' o 'ingresos'.
    - tipo: 'gastos' o 'ingresos'
    - incluir_historial: solo para ingresos; si True, incluye registros con es_historial=1
    En el caso de ingresos con incluir_historial=False, filtra es_historial=0.
    Retorna lista de tuplas según los campos de la tabla.
    """
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        if tipo == 'gastos':
            cursor.execute("SELECT id, nombre, monto, recurrente, fecha FROM gastos;")
            rows = cursor.fetchall()
        elif tipo == 'ingresos':
            if incluir_historial:
                cursor.execute("SELECT id, concepto, monto, fecha, es_historial FROM ingresos;")
            else:
                cursor.execute("SELECT id, concepto, monto, fecha FROM ingresos WHERE es_historial=0;")
            rows = cursor.fetchall()
        else:
            rows = []
        conn.close()
        return rows
    except Exception as e:
        print(f"Error al cargar datos de {tipo}:", e)
        return []

def eliminar_dato(tipo, campo, valor):
    """
    Elimina un registro de la tabla indicada ('gastos' o 'ingresos') donde campo=valor.
    Retorna True si borró alguna fila.
    """
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        query = f"DELETE FROM {tipo} WHERE {campo}=?;"
        cursor.execute(query, (valor,))
        filas = cursor.rowcount
        conn.commit()
        conn.close()
        return filas > 0
    except Exception as e:
        print(f"Error al eliminar dato de {tipo}:", e)
        return False

def eliminar_todos_datos():
    """
    Elimina todos los registros de ambas tablas 'gastos' e 'ingresos'.
    Retorna True si tuvo éxito.
    """
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM gastos;")
        cursor.execute("DELETE FROM ingresos;")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error al borrar todos los datos:", e)
        return False

# --- PARTE II: Lógica de negocio (gastos.py e ingresos.py) ---

def calcular_total_gastos():
    """
    Suma todos los montos de la tabla 'gastos'.
    """
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(monto) FROM gastos;")
        result = cursor.fetchone()
        total = result[0] if result and result[0] is not None else 0.0
        conn.close()
        return total
    except Exception as e:
        print("Error al calcular total gastos:", e)
        return 0.0

def calcular_total_ingresos():
    """
    Suma todos los montos de la tabla 'ingresos' con es_historial=0.
    """
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(monto) FROM ingresos WHERE es_historial=0;")
        result = cursor.fetchone()
        total = result[0] if result and result[0] is not None else 0.0
        conn.close()
        return total
    except Exception as e:
        print("Error al calcular total ingresos:", e)
        return 0.0

# --- PARTE III: Módulo IA simplificado (ia_module.py) ---

class ModuloIA:
    """
    Clase que simula la categorización de gastos según palabras clave.
    Este módulo lee un archivo de configuración JSON (ia_config.json) con categorías,
    pero aquí implementaremos un caso básico integrado:
      - 'alimentación': si contiene 'comida', 'restaurante', 'super'
      - 'vivienda': si contiene 'alquiler', 'luz', 'agua'
      - 'transporte': si contiene 'colectivo', 'taxi', 'nafta', 'combustible'
      - 'servicios': si contiene 'telefono', 'internet', 'gas'
      - 'ocio': si contiene 'cine', 'juego', 'salida'
      - 'salud': si contiene 'medico', 'farmacia', 'hospital'
      - 'educación': si contiene 'curso', 'libro', 'escuela'
      - 'otros': para todo lo que no encaje arriba
    """
    def __init__(self):
        # Palabras clave por categoría
        self.claves = {
            'alimentación': ['comida', 'restaurante', 'super', 'mercado', 'almuerzo', 'cena'],
            'vivienda': ['alquiler', 'luz', 'agua', 'internet', 'expensas'],
            'transporte': ['colectivo', 'taxi', 'nafta', 'combustible', 'subte', 'uber'],
            'servicios': ['telefono', 'gas', 'teléfono', 'servicio'],
            'ocio': ['cine', 'juego', 'salida', 'bar', 'pub'],
            'salud': ['médico', 'medico', 'farmacia', 'hospital'],
            'educación': ['curso', 'libro', 'escuela', 'universidad', 'clase'],
        }

    def categorizar(self, nombre_gasto):
        """
        Dada la descripción de un gasto, retorna la categoría correspondiente.
        """
        texto = nombre_gasto.lower()
        for categoria, lista_claves in self.claves.items():
            for palabra in lista_claves:
                if palabra in texto:
                    return categoria
        return 'otros'

    def procesar_gastos(self, lista_gastos):
        """
        Recibe lista de tuplas [(id, nombre, monto, recurrente, fecha), ...]
        Retorna lista de diccionarios con keys: id, nombre, monto, recurrente, fecha, categoria
        """
        resultado = []
        for gasto in lista_gastos:
            gid, nombre, monto, recurrente, fecha = gasto
            categoria = self.categorizar(nombre)
            resultado.append({
                'id': gid,
                'nombre': nombre,
                'monto': monto,
                'recurrente': bool(recurrente),
                'fecha': fecha,
                'categoria': categoria
            })
        return resultado

# Instancia singleton
modulo_ia = ModuloIA()

# --- PARTE IV: Interfaz Gráfica con Kivy ---

# Función para convertir hex a RGBA normalizado (0-1)
def hex_to_rgba(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)) + (1.0,)

# Paletas de colores para modo claro y modo oscuro
colors_light = {
    'fondo': hex_to_rgba('#fff0f5'),
    'panel': hex_to_rgba('#ffffff'),
    'acento': hex_to_rgba('#ff69b4'),
    'acento_oscuro': hex_to_rgba('#db7093'),
    'texto': hex_to_rgba('#4b0082'),
    'texto_suave': hex_to_rgba('#c71585'),
    'borde': hex_to_rgba('#ffe4e1'),
    'exito': hex_to_rgba('#98fb98'),
    'alerta': hex_to_rgba('#ff6347'),
    'destacado': hex_to_rgba('#ffd700'),
}
colors_dark = {
    'fondo': hex_to_rgba('#4b0082'),
    'panel': hex_to_rgba('#800080'),
    'acento': hex_to_rgba('#ff69b4'),
    'acento_oscuro': hex_to_rgba('#db7093'),
    'texto': hex_to_rgba('#fff0f5'),
    'texto_suave': hex_to_rgba('#ffc0cb'),
    'borde': hex_to_rgba('#c71585'),
    'exito': hex_to_rgba('#98fb98'),
    'alerta': hex_to_rgba('#ff6347'),
    'destacado': hex_to_rgba('#ffd700'),
}

class GastosScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        # Layout vertical principal
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        # Fondo de pantalla
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*self.app.current_colors['panel'])
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        # --- Formulario de entrada de gasto ---
        form = BoxLayout(orientation='vertical', size_hint_y=None)
        form.bind(minimum_height=form.setter('height'))

        lbl_title = Label(text="💰 Gastos", font_size=18, bold=True,
                          color=self.app.current_colors['texto'])
        form.add_widget(lbl_title)

        # Nombre del gasto
        box_nombre = BoxLayout(size_hint_y=None, height=30, padding=(0,5))
        lbl_nombre = Label(text="Nombre del gasto:", size_hint_x=0.4,
                            color=self.app.current_colors['texto'], font_size=14)
        self.input_nombre_gasto = TextInput(multiline=False, size_hint_x=0.6)
        box_nombre.add_widget(lbl_nombre)
        box_nombre.add_widget(self.input_nombre_gasto)
        form.add_widget(box_nombre)

        # Monto del gasto
        box_monto = BoxLayout(size_hint_y=None, height=30, padding=(0,5))
        lbl_monto = Label(text="Monto del gasto:", size_hint_x=0.4,
                           color=self.app.current_colors['texto'], font_size=14)
        self.input_monto_gasto = TextInput(multiline=False, size_hint_x=0.6,
                                           input_filter='float')
        box_monto.add_widget(lbl_monto)
        box_monto.add_widget(self.input_monto_gasto)
        form.add_widget(box_monto)

        # Fecha del gasto (opcional)
        box_fecha = BoxLayout(size_hint_y=None, height=30, padding=(0,5))
        lbl_fecha = Label(text="Fecha (YYYY-MM-DD):", size_hint_x=0.4,
                           color=self.app.current_colors['texto'], font_size=14)
        self.input_fecha_gasto = TextInput(multiline=False, size_hint_x=0.6)
        self.input_fecha_gasto.hint_text = "YYYY-MM-DD (opcional)"
        box_fecha.add_widget(lbl_fecha)
        box_fecha.add_widget(self.input_fecha_gasto)
        form.add_widget(box_fecha)

        # Checkbox recurrente
        box_rec = BoxLayout(size_hint_y=None, height=30, padding=(0,5))
        self.chk_recurrente = ToggleButton(text="Gasto recurrente", size_hint_x=0.5,
                                           group="recurr", background_normal='',
                                           background_down='', color=self.app.current_colors['texto'],
                                           background_color=self.app.current_colors['borde'])
        box_rec.add_widget(self.chk_recurrente)
        box_rec.add_widget(Label(text="", size_hint_x=0.5))
        form.add_widget(box_rec)

        # Botón Agregar Gasto
        btn_agregar = Button(text="Agregar Gasto", size_hint_y=None, height=40,
                              background_normal='', background_down='',
                              background_color=self.app.current_colors['acento'],
                              color=(1,1,1,1), bold=True)
        btn_agregar.bind(on_release=self.agregar_gasto)
        form.add_widget(btn_agregar)

        self.layout.add_widget(form)

        # --- Lista de gastos ---
        self.scroll = ScrollView(size_hint=(1, 1))
        self.list_container = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        self.scroll.add_widget(self.list_container)
        self.layout.add_widget(self.scroll)

        self.add_widget(self.layout)
        # Cargar datos iniciales
        self.actualizar_lista()

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def agregar_gasto(self, *args):
        nombre = self.input_nombre_gasto.text.strip()
        monto_text = self.input_monto_gasto.text.strip()
        fecha_text = self.input_fecha_gasto.text.strip()
        recurrente_flag = (self.chk_recurrente.state == 'down')
        if nombre == "":
            self.app.mostrar_error("El nombre del gasto no puede estar vacío.")
            return
        if monto_text == "":
            self.app.mostrar_error("El monto del gasto no puede estar vacío.")
            return
        try:
            monto = float(monto_text)
        except ValueError:
            self.app.mostrar_error("Monto inválido. Ingrese un número.")
            return
        if monto <= 0:
            self.app.mostrar_error("El monto debe ser mayor que cero.")
            return
        fecha = None
        if fecha_text:
            try:
                datetime.strptime(fecha_text, "%Y-%m-%d")
                fecha = fecha_text
            except ValueError:
                self.app.mostrar_error("Fecha inválida. Formato esperado YYYY-MM-DD.")
                return
        if guardar_gasto(nombre, monto, recurrente_flag, fecha):
            self.input_nombre_gasto.text = ""
            self.input_monto_gasto.text = ""
            self.input_fecha_gasto.text = ""
            self.chk_recurrente.state = 'normal'
            self.actualizar_lista()
        else:
            self.app.mostrar_error("No se pudo guardar el gasto. Verifique los datos.")

    def actualizar_lista(self):
        self.list_container.clear_widgets()
        gastos = cargar_datos('gastos')
        for gasto in gastos:
            gid = gasto[0]
            nombre = str(gasto[1])
            monto = gasto[2] if gasto[2] is not None else 0
            recurrente = bool(gasto[3]) if len(gasto) > 3 and gasto[3] is not None else False
            fecha = gasto[4] if len(gasto) > 4 and gasto[4] else ""
            monto_str = f"${monto:.2f}"
            rec_str = "✔" if recurrente else ""
            row = BoxLayout(size_hint_y=None, height=30)
            lbl_nombre = Label(text=nombre, size_hint_x=0.35, color=self.app.current_colors['texto'])
            lbl_monto = Label(text=monto_str, size_hint_x=0.15, color=self.app.current_colors['texto'])
            lbl_recur = Label(text=rec_str, size_hint_x=0.10, color=self.app.current_colors['texto'])
            lbl_fecha = Label(text=str(fecha), size_hint_x=0.30, color=self.app.current_colors['texto'])
            btn_del = Button(text="🗑️", size_hint_x=0.10, background_normal='', background_down='',
                              background_color=self.app.current_colors['alerta'], color=(1,1,1,1))
            btn_del.bind(on_release=partial(self.app.borrar_gasto, gid))
            row.add_widget(lbl_nombre)
            row.add_widget(lbl_monto)
            row.add_widget(lbl_recur)
            row.add_widget(lbl_fecha)
            row.add_widget(btn_del)
            self.list_container.add_widget(row)

class IngresosScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*self.app.current_colors['panel'])
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        # --- Formulario de ingreso ---
        form = BoxLayout(orientation='vertical', size_hint_y=None)
        form.bind(minimum_height=form.setter('height'))

        lbl_title = Label(text="💵 Ingresos", font_size=18, bold=True,
                          color=self.app.current_colors['texto'])
        form.add_widget(lbl_title)

        # Concepto
        box_concepto = BoxLayout(size_hint_y=None, height=30, padding=(0,5))
        lbl_concepto = Label(text="Concepto del ingreso:", size_hint_x=0.4,
                               color=self.app.current_colors['texto'], font_size=14)
        self.input_concepto_ingreso = TextInput(multiline=False, size_hint_x=0.6)
        box_concepto.add_widget(lbl_concepto)
        box_concepto.add_widget(self.input_concepto_ingreso)
        form.add_widget(box_concepto)

        # Monto
        box_monto = BoxLayout(size_hint_y=None, height=30, padding=(0,5))
        lbl_monto = Label(text="Monto del ingreso:", size_hint_x=0.4,
                           color=self.app.current_colors['texto'], font_size=14)
        self.input_monto_ingreso = TextInput(multiline=False, size_hint_x=0.6, input_filter='float')
        box_monto.add_widget(lbl_monto)
        box_monto.add_widget(self.input_monto_ingreso)
        form.add_widget(box_monto)

        # Botón Agregar Ingreso
        btn_agregar = Button(text="Agregar Ingreso", size_hint_y=None, height=40,
                              background_normal='', background_down='',
                              background_color=self.app.current_colors['acento'],
                              color=(1,1,1,1), bold=True)
        btn_agregar.bind(on_release=self.agregar_ingreso)
        form.add_widget(btn_agregar)

        # Botón Historial de Conceptos
        bottom_buttons = BoxLayout(size_hint_y=None, height=40, spacing=5)
        btn_historial = Button(text="📊 Historial", size_hint_x=0.5,
                                background_normal='', background_down='',
                                background_color=self.app.current_colors['acento_oscuro'],
                                color=(1,1,1,1))
        btn_historial.bind(on_release=self.ver_historial_conceptos)
        bottom_buttons.add_widget(btn_historial)
        bottom_buttons.add_widget(Label(text="", size_hint_x=0.5))
        form.add_widget(bottom_buttons)

        self.layout.add_widget(form)

        # --- Lista de ingresos ---
        self.scroll = ScrollView(size_hint=(1, 1))
        self.list_container = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        self.scroll.add_widget(self.list_container)
        self.layout.add_widget(self.scroll)

        self.add_widget(self.layout)
        self.actualizar_lista()

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def agregar_ingreso(self, *args):
        concepto = self.input_concepto_ingreso.text.strip()
        monto_text = self.input_monto_ingreso.text.strip()
        if concepto == "":
            self.app.mostrar_error("El concepto del ingreso no puede estar vacío.")
            return
        if monto_text == "":
            self.app.mostrar_error("El monto del ingreso no puede estar vacío.")
            return
        try:
            monto = float(monto_text)
        except ValueError:
            self.app.mostrar_error("Monto inválido. Ingrese un número.")
            return
        if monto <= 0:
            self.app.mostrar_error("El monto debe ser mayor que cero.")
            return
        if guardar_ingreso(concepto, monto):
            self.input_concepto_ingreso.text = ""
            self.input_monto_ingreso.text = ""
            self.actualizar_lista()
        else:
            self.app.mostrar_error("No se pudo guardar el ingreso. Verifique los datos.")

    def actualizar_lista(self):
        self.list_container.clear_widgets()
        ingresos = cargar_datos('ingresos')
        for ingreso in ingresos:
            iid = ingreso[0]
            concepto = str(ingreso[1])
            monto = ingreso[2] if ingreso[2] is not None else 0
            fecha = ingreso[3] if len(ingreso) > 3 and ingreso[3] else ""
            monto_str = f"${monto:.2f}"
            row = BoxLayout(size_hint_y=None, height=30)
            lbl_concepto = Label(text=concepto, size_hint_x=0.45,
                                   color=self.app.current_colors['texto'])
            lbl_monto = Label(text=monto_str, size_hint_x=0.20,
                               color=self.app.current_colors['texto'])
            lbl_fecha = Label(text=str(fecha), size_hint_x=0.25,
                               color=self.app.current_colors['texto'])
            btn_del = Button(text="🗑️", size_hint_x=0.10, background_normal='',
                              background_down='', background_color=self.app.current_colors['alerta'],
                              color=(1,1,1,1))
            btn_del.bind(on_release=partial(self.app.borrar_ingreso, iid))
            row.add_widget(lbl_concepto)
            row.add_widget(lbl_monto)
            row.add_widget(lbl_fecha)
            row.add_widget(btn_del)
            self.list_container.add_widget(row)

    def ver_historial_conceptos(self, *args):
        # Obtener todos los registros de ingresos (incluyendo historial)
        todos = cargar_datos('ingresos', incluir_historial=True)
        # Filtrar aquellos con es_historial=1 => monto==0 aquí
        conceptos_hist = [ing for ing in todos if len(ing) > 3 and ing[2] == 0]
        if not conceptos_hist:
            self.app.mostrar_info("No hay datos históricos de ingresos.")
            return
        stats_por_concepto = []
        # Agrupar ingresos reales por concepto
        for hist in conceptos_hist:
            concepto = hist[1]
            # Ingresos reales del mismo concepto
            ingresos_real = [ing for ing in cargar_datos('ingresos') if ing[1] == concepto and ing[2] and ing[2] > 0]
            montos = [ing[2] for ing in ingresos_real]
            if montos:
                cantidad = len(montos)
                total = sum(montos)
                promedio = total / cantidad
                minimo = min(montos)
                maximo = max(montos)
            else:
                cantidad, total, promedio, minimo, maximo = 0, 0, 0, 0, 0
            stats_por_concepto.append((concepto, {
                'cantidad': cantidad, 'total': total,
                'promedio': promedio, 'minimo': minimo, 'maximo': maximo
            }))
        texto = "[b]Historial de Conceptos de Ingresos:[/b]\n\n"
        for concepto, stats in stats_por_concepto:
            texto += f"[u]{concepto}[/u]: {stats['cantidad']} ingresos, Total ${stats['total']:.2f}, Promedio ${stats['promedio']:.2f}, Mínimo ${stats['minimo']:.2f}, Máximo ${stats['maximo']:.2f}\n"
        lbl = Label(text=texto, markup=True, valign='top')
        lbl.bind(size=lambda inst, size: inst.setter('text_size')(inst, (size[0]*0.95, None)))
        scrollview = ScrollView(size_hint=(1, 1))
        scrollview.add_widget(lbl)
        popup = Popup(title="Historial de Ingresos", content=scrollview, size_hint=(0.9, 0.9))
        popup.open()

class OrganizadorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modo_noche = False
        self.current_colors = colors_light.copy()

    def build(self):
        self.title = "Organizador de Gastos e Ingresos"
        root = BoxLayout(orientation='vertical', spacing=5)

        # ScreenManager con dos pantallas
        self.screen_manager = ScreenManager()
        self.gastos_screen = GastosScreen(app=self, name='gastos')
        self.ingresos_screen = IngresosScreen(app=self, name='ingresos')
        self.screen_manager.add_widget(self.gastos_screen)
        self.screen_manager.add_widget(self.ingresos_screen)

        # Barra de pestañas superior
        tab_bar = BoxLayout(size_hint_y=None, height=40, padding=(5,0), spacing=5)
        self.tab_gastos_btn = ToggleButton(text="Gastos", group="tabs", state="down",
                                           background_normal='', background_down='',
                                           background_color=self.current_colors['acento'],
                                           color=(1,1,1,1), bold=True)
        self.tab_ingresos_btn = ToggleButton(text="Ingresos", group="tabs", state="normal",
                                             background_normal='', background_down='',
                                             background_color=self.current_colors['acento_oscuro'],
                                             color=(1,1,1,1), bold=True)
        self.tab_gastos_btn.bind(on_release=lambda *args: self.cambiar_pantalla('gastos'))
        self.tab_ingresos_btn.bind(on_release=lambda *args: self.cambiar_pantalla('ingresos'))
        tab_bar.add_widget(self.tab_gastos_btn)
        tab_bar.add_widget(self.tab_ingresos_btn)

        spacer = Label(text="", size_hint_x=1)
        self.btn_modo = Button(text="🌙", size_hint_x=None, width=40,
                                background_normal='', background_down='',
                                background_color=self.current_colors['borde'],
                                color=self.current_colors['texto'])
        self.btn_modo.bind(on_release=self.toggle_modo_noche)
        tab_bar.add_widget(spacer)
        tab_bar.add_widget(self.btn_modo)

        # Barra inferior de acciones
        bottom_bar = BoxLayout(size_hint_y=None, height=50, padding=5, spacing=5)
        btn_balance = Button(text="📊 Balance", background_normal='', background_down='',
                              background_color=self.current_colors['acento'], color=(1,1,1,1), bold=True)
        btn_balance.bind(on_release=self.mostrar_balance_total)
        btn_presupuesto = Button(text="💰 Presup. IA", background_normal='', background_down='',
                                   background_color=self.current_colors['acento'], color=(1,1,1,1), bold=True)
        btn_presupuesto.bind(on_release=self.mostrar_presupuesto_inteligente)
        btn_dolar = Button(text="💵 Dólar", background_normal='', background_down='',
                             background_color=self.current_colors['acento_oscuro'], color=(1,1,1,1), bold=True)
        btn_dolar.bind(on_release=self.mostrar_cotizacion_dolar)
        btn_borrar = Button(text="🗑️ Borrar Todo", background_normal='', background_down='',
                              background_color=self.current_colors['alerta'], color=(1,1,1,1), bold=True)
        btn_borrar.bind(on_release=self.confirmar_borrar_todo)
        bottom_bar.add_widget(btn_balance)
        bottom_bar.add_widget(btn_presupuesto)
        bottom_bar.add_widget(btn_dolar)
        bottom_bar.add_widget(btn_borrar)

        root.add_widget(tab_bar)
        root.add_widget(self.screen_manager)
        root.add_widget(bottom_bar)
        return root

    def cambiar_pantalla(self, nombre_pantalla):
        self.screen_manager.current = nombre_pantalla
        if nombre_pantalla == 'gastos':
            self.tab_gastos_btn.background_color = self.current_colors['acento']
            self.tab_ingresos_btn.background_color = self.current_colors['acento_oscuro']
            self.tab_gastos_btn.state = 'down'
            self.tab_ingresos_btn.state = 'normal'
        else:
            self.tab_gastos_btn.background_color = self.current_colors['acento_oscuro']
            self.tab_ingresos_btn.background_color = self.current_colors['acento']
            self.tab_gastos_btn.state = 'normal'
            self.tab_ingresos_btn.state = 'down'

    def borrar_gasto(self, gid, *args):
        if eliminar_dato('gastos', 'id', gid):
            self.gastos_screen.actualizar_lista()

    def borrar_ingreso(self, iid, *args):
        if eliminar_dato('ingresos', 'id', iid):
            self.ingresos_screen.actualizar_lista()

    def confirmar_borrar_todo(self, *args):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        lbl = Label(text="¿Seguro que desea borrar TODOS los datos?\nEsta acción no se puede deshacer.",
                    color=self.current_colors['texto'], halign='center')
        content.add_widget(lbl)
        btns = BoxLayout(size_hint_y=None, height=40, spacing=10)
        btn_si = Button(text="Sí", background_color=self.current_colors['alerta'], color=(1,1,1,1),
                         background_normal='', background_down='')
        btn_no = Button(text="No", background_color=self.current_colors['acento'], color=(1,1,1,1),
                         background_normal='', background_down='')
        btns.add_widget(btn_si)
        btns.add_widget(btn_no)
        content.add_widget(btns)
        popup = Popup(title="Confirmar Acción", content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        btn_no.bind(on_release=lambda *args: popup.dismiss())
        btn_si.bind(on_release=lambda *args: self._borrar_todo(popup))
        popup.open()

    def _borrar_todo(self, popup):
        popup.dismiss()
        if eliminar_todos_datos():
            self.gastos_screen.actualizar_lista()
            self.ingresos_screen.actualizar_lista()
            self.mostrar_info("Todos los datos han sido borrados exitosamente.")
        else:
            self.mostrar_error("Error al borrar los datos.")

    def mostrar_balance_total(self, *args):
        total_gastos = calcular_total_gastos()
        total_ingresos = calcular_total_ingresos()
        balance = total_ingresos - total_gastos
        mensaje_balance = f"Total de Ingresos: ${total_ingresos:.2f}\n"
        mensaje_balance += f"Total de Gastos: ${total_gastos:.2f}\n"
        mensaje_balance += f"Balance Final: ${balance:.2f}\n\n"
        if balance >= 0:
            mensaje_balance += "✅ Tus finanzas están equilibradas o en positivo.\n"
        else:
            mensaje_balance += "⚠️ Tus gastos superan tus ingresos.\n"
        recomendaciones = []
        if balance <= 0:
            recomendaciones = [
                "• Reduce gastos no esenciales.",
                "• Prioriza pagos urgentes primero.",
                "• Evita adquirir nuevas deudas."
            ]
        else:
            ahorro = balance * 0.20
            emergencia = balance * 0.10
            inversion = balance * 0.15
            gasto_futuro = balance * 0.55
            recomendaciones = [
                f"• Ahorra ~20% (${ahorro:.2f}) para objetivos largos.",
                f"• Reserva ~10% (${emergencia:.2f}) como fondo de emergencia.",
                f"• Considera invertir ~15% (${inversion:.2f}) en opciones seguras.",
                f"• Destina ~55% (${gasto_futuro:.2f}) para gastos futuros."
            ]
        texto = f"[b]Balance Total[/b]\n{mensaje_balance}\n[b]Recomendaciones:[/b]\n" + "\n".join(recomendaciones)
        lbl = Label(text=texto, markup=True)
        lbl.text_size = (400, None)
        lbl.valign = 'middle'
        lbl.halign = 'left'
        popup = Popup(title="Balance y Recomendaciones", content=lbl, size_hint=(0.9, 0.6))
        popup.open()

    def mostrar_presupuesto_inteligente(self, *args):
        gastos_raw = cargar_datos('gastos')
        gastos_procesados = modulo_ia.procesar_gastos(gastos_raw)
        categorias_totales = {}
        total_gastos = 0.0
        for g in gastos_procesados:
            cat = g.get('categoria', 'otros')
            monto = g.get('monto', 0.0)
            total_gastos += monto
            categorias_totales[cat] = categorias_totales.get(cat, 0.0) + monto

        ingresos_raw = cargar_datos('ingresos')
        total_ingresos = sum(ing[2] for ing in ingresos_raw if ing[2] is not None)

        ideales = {
            'alimentación': 25, 'vivienda': 30, 'transporte': 15, 'servicios': 10,
            'ocio': 5, 'salud': 5, 'educación': 5, 'ahorro': 10, 'otros': 5
        }
        texto = "[b]Presupuesto Inteligente - Distribución de Gastos[/b]\n\n"
        for categoria, ideal_pct in ideales.items():
            if categoria == 'ahorro':
                actual_pct = ((total_ingresos - total_gastos) / total_ingresos * 100.0) if total_ingresos > total_gastos and total_ingresos > 0 else 0.0
            else:
                actual_pct = ((categorias_totales.get(categoria, 0.0) / total_gastos) * 100.0) if total_gastos > 0 else 0.0
            actual_pct = round(actual_pct, 1)
            ideal_pct = float(ideal_pct)
            texto += f"{categoria.capitalize():<12}: Actual {actual_pct:.1f}%  |  Ideal {ideal_pct:.1f}%"
            if actual_pct > ideal_pct + 5:
                texto += "  ⚠️ Sobre el ideal\n"
            elif actual_pct < ideal_pct - 5:
                texto += "  📉 Bajo el ideal\n"
            else:
                texto += "  ✅ Dentro del rango ideal\n"
        lbl = Label(text=texto, markup=True)
        lbl.text_size = (500, None)
        lbl.halign = 'left'
        lbl.valign = 'top'
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(lbl)
        popup = Popup(title="Presupuesto Inteligente", content=scroll, size_hint=(0.95, 0.8))
        popup.open()

    def mostrar_cotizacion_dolar(self, *args):
        self.dolar_popup = Popup(title="Cotización del Dólar", size_hint=(0.9, 0.6))
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.lbl_dolar_info = Label(text="Obteniendo cotizaciones...", halign='center')
        popup_layout.add_widget(self.lbl_dolar_info)
        btn_cerrar = Button(text="Cerrar", size_hint_y=None, height=40,
                              background_normal='', background_down='',
                              background_color=self.current_colors['acento'], color=(1,1,1,1))
        btn_cerrar.bind(on_release=lambda *args: self.dolar_popup.dismiss())
        popup_layout.add_widget(btn_cerrar)
        self.dolar_popup.content = popup_layout
        self.dolar_popup.open()
        threading.Thread(target=self._fetch_dolar_data, daemon=True).start()

    def _fetch_dolar_data(self):
        try:
            resp = requests.get("https://api.bluelytics.com.ar/v2/latest", timeout=5)
            datos = {
                'oficial': {'compra': '---', 'venta': '---'},
                'blue': {'compra': '---', 'venta': '---'},
                'bolsa': {'compra': '---', 'venta': '---'},
                'ccl': {'compra': '---', 'venta': '---'},
                'turista': {'compra': '---', 'venta': '---'}
            }
            if resp.status_code == 200:
                data_json = resp.json()
                datos['oficial']['compra'] = str(data_json['oficial']['value_buy'])
                datos['oficial']['venta'] = str(data_json['oficial']['value_sell'])
                datos['blue']['compra'] = str(data_json['blue']['value_buy'])
                datos['blue']['venta'] = str(data_json['blue']['value_sell'])
                valor_oficial = float(data_json['oficial']['value_sell'])
                datos['bolsa']['compra'] = str(round(valor_oficial * 0.98, 2))
                datos['bolsa']['venta'] = str(round(valor_oficial * 1.03, 2))
                datos['ccl']['compra'] = str(round(valor_oficial * 0.99, 2))
                datos['ccl']['venta'] = str(round(valor_oficial * 1.04, 2))
                datos['turista']['venta'] = str(round(valor_oficial * 1.30, 2))
            try:
                resp2 = requests.get("https://dolarapi.com/v1/dolares", timeout=5)
                if resp2.status_code == 200:
                    data2 = resp2.json()
                    for item in data2:
                        casa = item.get("casa", "").lower()
                        if casa in ["oficial", "oficial_euro", "oficial dolar"]:
                            datos['oficial']['compra'] = item.get("compra", datos['oficial']['compra'])
                            datos['oficial']['venta'] = item.get("venta", datos['oficial']['venta'])
                        elif casa in ["blue", "dolar blue"]:
                            datos['blue']['compra'] = item.get("compra", datos['blue']['compra'])
                            datos['blue']['venta'] = item.get("venta", datos['blue']['venta'])
                        elif casa in ["bolsa", "mep"]:
                            datos['bolsa']['compra'] = item.get("compra", datos['bolsa']['compra'])
                            datos['bolsa']['venta'] = item.get("venta", datos['bolsa']['venta'])
                        elif casa in ["contadoconliqui", "ccl"]:
                            datos['ccl']['compra'] = item.get("compra", datos['ccl']['compra'])
                            datos['ccl']['venta'] = item.get("venta", datos['ccl']['venta'])
                        elif casa in ["turista", "tarjeta"]:
                            datos['turista']['venta'] = item.get("venta", datos['turista']['venta'])
            except Exception as e:
                print("No se pudieron obtener datos de la API alternativa:", e)
            info_text = ("[b]Dólar Oficial:[/b] Compra ${} - Venta ${}\n"
                         "[b]Dólar Blue:[/b] Compra ${} - Venta ${}\n"
                         "[b]Dólar Bolsa/MEP:[/b] Compra ${} - Venta ${}\n"
                         "[b]Dólar CCL:[/b] Compra ${} - Venta ${}\n"
                         "[b]Dólar Turista:[/b] Venta ${}\n").format(
                            datos['oficial']['compra'], datos['oficial']['venta'],
                            datos['blue']['compra'], datos['blue']['venta'],
                            datos['bolsa']['compra'], datos['bolsa']['venta'],
                            datos['ccl']['compra'], datos['ccl']['venta'],
                            datos['turista']['venta'])
            Clock.schedule_once(lambda dt: self._actualizar_dolar_popup(info_text), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._actualizar_dolar_popup("Error al obtener cotizaciones.\nIntente más tarde."), 0)
            print("Error en _fetch_dolar_data:", e)

    def _actualizar_dolar_popup(self, info_text):
        if hasattr(self, 'lbl_dolar_info'):
            self.lbl_dolar_info.text = info_text

    def mostrar_info(self, mensaje):
        popup = Popup(title="Información",
                      content=Label(text=mensaje, halign='center'),
                      size_hint=(0.8, 0.3))
        popup.open()

    def mostrar_error(self, mensaje):
        popup = Popup(title="Error",
                      content=Label(text=mensaje, halign='center', color=(1,0,0,1)),
                      size_hint=(0.8, 0.3))
        popup.open()

    def toggle_modo_noche(self, *args):
        self.modo_noche = not self.modo_noche
        self.current_colors = colors_dark.copy() if self.modo_noche else colors_light.copy()
        self.tab_gastos_btn.color = (1,1,1,1)
        self.tab_ingresos_btn.color = (1,1,1,1)
        self.btn_modo.text = "☀️" if self.modo_noche else "🌙"
        self.btn_modo.background_color = self.current_colors['borde']
        self.btn_modo.color = self.current_colors['texto']
        for screen in [self.gastos_screen, self.ingresos_screen]:
            screen.canvas.before.children[0].rgba = self.current_colors['panel']
            for child in screen.layout.walk(restrict=True):
                if isinstance(child, Label):
                    child.color = self.current_colors['texto']
        self.cambiar_pantalla(self.screen_manager.current)

# Ejecutar la aplicación
if __name__ == '__main__':
    OrganizadorApp().run()
