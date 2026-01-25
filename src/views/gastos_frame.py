# ui/frames/gastos_frame.py
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import locale
import csv
import os
import threading
import logging
from functools import lru_cache

from src.models.ia_module import modulo_ia
from src.models.data_manager import (
    cargar_datos,
    guardar_gasto,
    eliminar_dato,
    cargar_historial_gastos,
    obtener_estadisticas_gasto,
    obtener_info_gasto_historial,
)
from src.utils.utils import ThreadManager

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='gastos_frame.log'
)
logger = logging.getLogger('gastos_frame')

class GastosFrame(tk.Frame):
    def __init__(self, parent, controller):
        self.controller = controller
        colores = controller.colores['claro']
        
        # Crear un frame con borde y esquinas redondeadas (efecto panel)
        super().__init__(
            parent, 
            bg=colores['panel'],
            # highlightbackground=  # No soportado en este tema Linux, colores['borde'],
            highlightthickness=1,
            padx=15, 
            pady=15,
            relief=tk.RAISED,
            bd=0
        )
        
        # Configurar locale para fechas en español argentino de manera segura
        self._configurar_locale()
        
        # Cargar datos en un hilo separado para no bloquear la UI
        self.nombres_gastos_historicos = []
        self.carga_finalizada = threading.Event()
        threading.Thread(target=self._cargar_datos_en_hilo, daemon=True).start()
        
        # Crear widgets para gastos
        self.crear_widgets()
        
        # Mostrar indicador de carga
        self.mostrar_indicador_carga()

        self.after(100, self._verificar_carga_datos)

    def _configurar_locale(self):
        """Configura el locale para fechas en español de manera segura"""
        try:
            locale.setlocale(locale.LC_TIME, 'es_AR.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Alternativa
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_TIME, 'es.UTF-8')  # Más genérico
                except locale.Error:
                    logger.warning("No se pudo configurar el locale en español. Se usará el predeterminado.")

    def _cargar_datos_en_hilo(self):
        """Carga los datos históricos en un hilo separado"""
        try:
            logger.info("Iniciando carga de nombres de gastos históricos")
            self.nombres_gastos_historicos = self.cargar_nombres_gastos_historicos()
            logger.info(f"{len(self.nombres_gastos_historicos)} nombres cargados")
            
            # CAMBIO: No actualizar la UI directamente desde otro hilo
            # Usar una variable de control para indicar que la carga está completa
            self.carga_finalizada.set()
                
        except Exception as e:
            logger.error(f"Error al cargar datos históricos: {e}")
            self.nombres_gastos_historicos = []
            self.carga_finalizada.set()

    def _verificar_carga_datos(self):
        """Verifica si los datos se han cargado para actualizar la UI"""
        if self.carga_finalizada.is_set():
            # Actualizar combobox con valores
            if self.nombres_gastos_historicos:
                self.combo_gasto_nombre['values'] = self.nombres_gastos_historicos
            self.quitar_indicador_carga()
        else:
            # Verificar nuevamente después de 100ms
            self.after(100, self._verificar_carga_datos)

    def mostrar_indicador_carga(self):
        """Muestra un indicador de carga mientras se cargan los datos"""
        if not hasattr(self, 'frame_carga'):
            self.frame_carga = tk.Frame(self, bg=self.controller.colores['claro']['panel'])
            self.frame_carga.place(relx=0.5, rely=0.3, anchor=tk.CENTER)
            
            tk.Label(
                self.frame_carga,
                text="Cargando datos...",
                font=("Comic Sans MS", 10, "italic"),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel']
            ).pack(pady=5)

    def quitar_indicador_carga(self):
        """Quita el indicador de carga"""
        if hasattr(self, 'frame_carga'):
            self.frame_carga.destroy()
            delattr(self, 'frame_carga')

    def auto_categorizar_gasto(self, nombre_gasto):
        """Categoriza automáticamente un gasto usando el módulo IA"""
        return modulo_ia.categorizar_gasto(nombre_gasto)

    def agregar_gasto(self):
        """Agrega un nuevo gasto a la base de datos con categorización automática"""
        # Obtener el modo actual para los colores
        modo = 'oscuro' if self.controller.modo_noche else 'claro'
        colores = self.controller.colores[modo]
        
        # Obtener valores de los campos
        nombre = self.combo_gasto_nombre.get().strip()
        monto_str = self.entry_gasto_monto.get().strip()
        
        # Validar que el nombre no esté vacío
        if not nombre:
            messagebox.showerror("Error", "Debe ingresar un nombre para el gasto.")
            self.combo_gasto_nombre.focus_set()
            return
        
        # Validar y convertir el monto
        try:
            monto = float(monto_str.replace(',', '.'))  # Reemplazar coma por punto para usuarios argentinos
            if monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor que cero.")
                self.entry_gasto_monto.focus_set()
                return
        except ValueError:
            messagebox.showerror("Error", "Monto inválido. Por favor, ingrese un número válido.")
            self.entry_gasto_monto.focus_set()
            return
        
        # Obtener estado del checkbox (recurrente o no)
        recurrente = self.chk_var_recurrente.get() == 1
        
        # Obtener la fecha seleccionada del DateEntry
        fecha_seleccionada = self.date_selector.get_date()
        fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
        
        # Categorizar automáticamente en un hilo separado para no bloquear la UI
        threading.Thread(
            target=self._procesar_guardado_gasto,
            args=(nombre, monto, recurrente, fecha_str),
            daemon=True
        ).start()
        
        # Mostrar indicador de procesamiento
        self.combo_gasto_nombre.config(state="disabled")
        self.entry_gasto_monto.config(state="disabled")
        self.btn_agregar_gasto.config(state="disabled", text="Procesando...")

    def _procesar_guardado_gasto(self, nombre, monto, recurrente, fecha_str):
        """Procesa el guardado del gasto en un hilo separado"""
        try:
            # Categorizar
            categoria = self.auto_categorizar_gasto(nombre)
            
            # Guardar el gasto en la base de datos
            if guardar_gasto(nombre, monto, recurrente, fecha_str):
                # Mensaje para mostrar
                mensaje = f"✅ El gasto '{nombre}' de ${monto:.2f} ha sido registrado correctamente."
                if categoria != 'otros':
                    mensaje += f"\n\nCategoría detectada: {categoria}"
                
                # Actualizar la UI en el hilo principal
                self.after(0, lambda: self._actualizar_ui_despues_guardar(True, mensaje, nombre))
            else:
                # Actualizar la UI en caso de error
                self.after(0, lambda: self._actualizar_ui_despues_guardar(
                    False, "No se pudo guardar el gasto. Intente nuevamente.", nombre))
        except Exception as e:
            logger.error(f"Error al guardar gasto: {e}")
            # Actualizar la UI en caso de error
            self.after(0, lambda: self._actualizar_ui_despues_guardar(
                False, f"Ocurrió un error al guardar el gasto: {str(e)}", nombre))

    def _actualizar_ui_despues_guardar(self, exito, mensaje, nombre):
        """Actualiza la UI después de guardar un gasto"""
        # Restaurar estados de widgets
        self.combo_gasto_nombre.config(state="normal")  # Cambiado de "readonly" a "normal"
        self.entry_gasto_monto.config(state="normal")
        self.btn_agregar_gasto.config(state="normal", text="➕ Agregar")
        
        if exito:
            messagebox.showinfo("Gasto Registrado", mensaje)
            
            # Limpiar los campos
            self.combo_gasto_nombre.set("")
            self.entry_gasto_monto.delete(0, tk.END)
            self.chk_var_recurrente.set(0)
            self.combo_gasto_nombre.focus_set()
            
            # Actualizar la lista de nombres de gastos históricos en un hilo separado
            threading.Thread(target=self._actualizar_nombres_historicos, daemon=True).start()
        else:
            messagebox.showerror("Error", mensaje)

    def _actualizar_nombres_historicos(self):
        """Actualiza la lista de nombres históricos en un hilo separado"""
        try:
            # Limpiar caché para forzar recarga
            if hasattr(cargar_historial_gastos, 'cache_clear'):
                cargar_historial_gastos.cache_clear()
                
            nuevos_nombres = self.cargar_nombres_gastos_historicos()
            
            # Actualizar combo en el hilo principal
            self.after(0, lambda: self.actualizar_combo_nombres(nuevos_nombres))
        except Exception as e:
            logger.error(f"Error al actualizar nombres históricos: {e}")

    def actualizar_combo_nombres(self, nuevos_nombres):
        """Actualiza el combobox con los nuevos nombres"""
        self.nombres_gastos_historicos = nuevos_nombres
        if hasattr(self, 'combo_gasto_nombre'):
            self.combo_gasto_nombre['values'] = nuevos_nombres
        
    def crear_widgets(self):
        colores = self.controller.colores['claro']
        
        # Título de la sección con icono
        title_frame = tk.Frame(self, bg=colores['panel'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.label_gasto = tk.Label(
            title_frame, 
            text="💰 Gastos", 
            font=("Comic Sans MS", 14, "bold"), 
            fg=colores['texto'],
            bg=colores['panel']
        )
        self.label_gasto.pack(anchor=tk.W)
        
        # Línea divisoria
        separator = ttk.Separator(title_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(5, 0))
        
        # Crear frame para formulario con margen
        form_frame = tk.Frame(self, bg=colores['panel'], pady=10)
        form_frame.pack(fill=tk.X)
        
        # Nombre del gasto con historial
        self.label_gasto_nombre = tk.Label(
            form_frame, 
            text="Nombre del gasto:", 
            font=("Comic Sans MS", 12), 
            fg=colores['texto'],
            bg=colores['panel'],
            anchor=tk.W
        )
        self.label_gasto_nombre.pack(fill=tk.X, pady=(10, 5))
        
        # Usar un combobox con mejor estilo para el historial
        self.combo_style = ttk.Style()
        self.combo_style.configure('TCombobox', padding=5)
        
        self.combo_gasto_nombre = ttk.Combobox(
            form_frame, 
            values=self.nombres_gastos_historicos, 
            font=("Comic Sans MS", 12),
            height=10,
            state="normal"  # Cambiado de "readonly" a "normal"
        )
        self.combo_gasto_nombre.pack(fill=tk.X)
        
        # Monto del gasto
        self.label_gasto_monto = tk.Label(
            form_frame, 
            text="Monto del gasto:", 
            font=("Comic Sans MS", 12), 
            fg=colores['texto'],
            bg=colores['panel'],
            anchor=tk.W
        )
        self.label_gasto_monto.pack(fill=tk.X, pady=(10, 5))
        
        self.entry_gasto_monto = tk.Entry(
            form_frame, 
            font=("Comic Sans MS", 12),
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1,
            # highlightbackground=  # No soportado en este tema Linux, colores['borde']
        )
        self.entry_gasto_monto.pack(fill=tk.X)
        
        # Fecha del gasto (reemplazando la fecha automática con un selector)
        self.label_fecha_gasto = tk.Label(
            form_frame, 
            text="Fecha del gasto:", 
            font=("Comic Sans MS", 12), 
            fg=colores['texto'],
            bg=colores['panel'],
            anchor=tk.W
        )
        self.label_fecha_gasto.pack(fill=tk.X, pady=(10, 5))
        
        # Frame para el selector de fecha
        fecha_frame = tk.Frame(form_frame, bg=colores['panel'])
        fecha_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Selector de fecha con formato argentino (dd/mm/yyyy)
        fecha_actual = datetime.now()
        self.date_selector = DateEntry(
            fecha_frame,
            width=12,
            background=colores['acento'],
            foreground='white',
            borderwidth=2,
            year=fecha_actual.year,
            month=fecha_actual.month,
            day=fecha_actual.day,
            font=("Comic Sans MS", 12),
            date_pattern='dd/mm/yyyy',  # Formato argentino
            selectbackground=colores['acento_oscuro'],
            selectforeground='white',
            locale='es_ES'  # Usar español si está disponible
        )
        self.date_selector.pack(side=tk.LEFT)
        
        # Información adicional
        tk.Label(
            fecha_frame,
            text="Haz clic para seleccionar una fecha",
            font=("Comic Sans MS", 9, "italic"),
            fg=colores['texto_suave'],
            bg=colores['panel']
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Checkbox para gastos recurrentes con mejor estilo
        self.chk_var_recurrente = tk.IntVar()
        self.chk_recurrente = tk.Checkbutton(
            form_frame, 
            text="Gasto recurrente", 
            variable=self.chk_var_recurrente, 
            font=("Comic Sans MS", 12),
            fg=colores['texto'],
            bg=colores['panel'],
            activebackground=colores['panel'],
            selectcolor=colores['panel']
        )
        self.chk_recurrente.pack(anchor=tk.W, pady=10)
        
        # Frame para botones con mejor distribución
        buttons_frame = tk.Frame(self, bg=colores['panel'])
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Primera fila de botones
        top_buttons = tk.Frame(buttons_frame, bg=colores['panel'])
        top_buttons.pack(fill=tk.X, pady=(0, 5))
        
        # Botones de acción con íconos y mejor estilo
        self.btn_agregar_gasto = tk.Button(
            top_buttons, 
            text="➕ Agregar", 
            command=self.agregar_gasto, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['exito'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_agregar_gasto.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.round_button(self.btn_agregar_gasto)
        
        self.btn_eliminar_gasto = tk.Button(
            top_buttons, 
            text="❌ Eliminar", 
            command=self.eliminar_gasto, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['alerta'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_eliminar_gasto.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.round_button(self.btn_eliminar_gasto)
        
        # Segunda fila de botones
        bottom_buttons = tk.Frame(buttons_frame, bg=colores['panel'])
        bottom_buttons.pack(fill=tk.X)
        
        self.btn_mostrar_gastos = tk.Button(
            bottom_buttons, 
            text="📋 Mostrar Gastos", 
            command=self.mostrar_gastos, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['acento'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_mostrar_gastos.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.round_button(self.btn_mostrar_gastos)
        
        self.btn_historial_gastos = tk.Button(
            bottom_buttons, 
            text="📊 Historial", 
            command=self.mostrar_historial_gastos, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['destacado'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_historial_gastos.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.round_button(self.btn_historial_gastos)
        
        # Vincular la tecla Enter para agregar un gasto
        self.entry_gasto_monto.bind('<Return>', self.agregar_gasto_event)
        
        # Vincular evento de selección del combobox
        self.combo_gasto_nombre.bind('<<ComboboxSelected>>', self.gasto_seleccionado)
        
        # Vincular evento de escritura para autocompletado
        self.combo_gasto_nombre.bind('<KeyRelease>', self.autocompletar_gasto)
        
        # Verificar carga de datos antes de mostrar
        self._verificar_carga_datos()
    
    def _verificar_carga_datos(self):
        """Verifica si los datos se han cargado para actualizar la UI"""
        if self.carga_finalizada.is_set():
            # Actualizar combobox con valores
            if self.nombres_gastos_historicos:
                self.combo_gasto_nombre['values'] = self.nombres_gastos_historicos
            self.quitar_indicador_carga()
        else:
            # Verificar nuevamente después de 100ms
            self.after(100, self._verificar_carga_datos)
    
    @lru_cache(maxsize=128)
    def cargar_nombres_gastos_historicos(self):
        """Carga el historial de nombres de gastos para el combobox"""
        try:
            # Obtener nombres únicos de la base de datos
            nombres = cargar_historial_gastos()
            return nombres if nombres else []
        except Exception as e:
            logger.error(f"Error al cargar historial de gastos: {e}")
            return []
    
    def autocompletar_gasto(self, event=None):
        """Autocompletado para el combobox de gastos"""
        try:
            valor_actual = self.combo_gasto_nombre.get().lower()
            
            # Si está vacío, mostrar todos
            if not valor_actual:
                self.combo_gasto_nombre['values'] = self.nombres_gastos_historicos
                return
            
            # Filtrar los valores que coincidan
            opciones_filtradas = [
                opt for opt in self.nombres_gastos_historicos 
                if opt.lower().startswith(valor_actual)
            ]
            
            # Actualizar el combobox con las opciones filtradas
            self.combo_gasto_nombre['values'] = opciones_filtradas
            
            # Si hay una coincidencia perfecta, marcar como seleccionada
            if valor_actual in [opt.lower() for opt in self.nombres_gastos_historicos]:
                # Buscar la opción exacta preservando mayúsculas
                for opt in self.nombres_gastos_historicos:
                    if opt.lower() == valor_actual:
                        self.combo_gasto_nombre.set(opt)
                        break
        except Exception as e:
            logger.error(f"Error en autocompletado: {e}")
    
    def gasto_seleccionado(self, event):
        """Maneja la selección de un gasto desde el historial"""
        # Obtener el nombre de gasto seleccionado
        nombre = self.combo_gasto_nombre.get()
        if not nombre:
            return
        
        # Buscar en caché primero
        if hasattr(self, '_cache_estadisticas') and nombre in self._cache_estadisticas:
            self._aplicar_estadisticas_gasto(nombre, self._cache_estadisticas[nombre])
            return
            
        # Obtener estadísticas en un hilo separado para no bloquear la UI
        threading.Thread(
            target=self._obtener_estadisticas_en_hilo,
            args=(nombre,),
            daemon=True
        ).start()
    
    def _obtener_estadisticas_en_hilo(self, nombre):
        """Obtiene estadísticas de un gasto en un hilo separado"""
        try:
            # Obtener estadísticas
            estadisticas = obtener_estadisticas_gasto(nombre)
            
            # Guardar en caché
            if not hasattr(self, '_cache_estadisticas'):
                self._cache_estadisticas = {}
            self._cache_estadisticas[nombre] = estadisticas
            
            # Actualizar UI en hilo principal
            self.after(0, lambda: self._aplicar_estadisticas_gasto(nombre, estadisticas))
        except Exception as e:
            logger.error(f"Error al obtener estadísticas del gasto: {e}")
    
    def _aplicar_estadisticas_gasto(self, nombre, estadisticas):
        """Aplica las estadísticas obtenidas a la UI"""
        if estadisticas['cantidad'] > 0:
            # Sugerir el monto promedio del gasto seleccionado
            self.entry_gasto_monto.delete(0, tk.END)
            self.entry_gasto_monto.insert(0, f"{estadisticas['promedio']:.2f}")
                
            # Marcar el checkbox según estadísticas
            self.chk_var_recurrente.set(1 if estadisticas['recurrente'] else 0)
        else:
            # Si no hay transacciones, al menos configurar la recurrencia
            info = obtener_info_gasto_historial(nombre)
            self.chk_var_recurrente.set(1 if info['recurrente'] else 0)
    
    def round_button(self, button):
        """Aplica estilo redondeado a los botones"""
        try:
            button.config(relief=tk.FLAT, borderwidth=0)
            # Intentar configuraciones adicionales para bordes redondeados
            if hasattr(button, 'config') and callable(getattr(button.config, '__call__', None)):
                button.config(highlightthickness=0)
        except Exception as e:
            logger.error(f"No se pudieron aplicar bordes redondeados: {e}")

    def mostrar_gastos(self):
        """Muestra una ventana con la lista completa de gastos"""
        # Crear una ventana emergente
        ventana_gastos = tk.Toplevel(self)
        ventana_gastos.title("Lista de Gastos")
        ventana_gastos.geometry("900x600")
        ventana_gastos.configure(bg=self.controller.colores['claro']['panel'])
        
        # Hacer la ventana modal
        ventana_gastos.transient(self.controller.root)
        ventana_gastos.grab_set()
        ventana_gastos.focus_set()
        
        # Mostrar mensaje de carga
        loading_label = tk.Label(
            ventana_gastos,
            text="Cargando datos...",
            font=("Comic Sans MS", 12),
            fg=self.controller.colores['claro']['texto'],
            bg=self.controller.colores['claro']['panel']
        )
        loading_label.pack(expand=True, pady=20)
        
        # Cargar gastos en un hilo separado
        def cargar_gastos_en_hilo():
            try:
                # Obtener datos
                datos_gastos = cargar_datos('gastos')
                
                # Actualizar UI en hilo principal
                ventana_gastos.after(0, lambda: mostrar_datos_gastos(datos_gastos))
            except Exception as e:
                logger.error(f"Error al cargar gastos: {e}")
                ventana_gastos.after(0, lambda: messagebox.showerror("Error", f"No se pudieron cargar los gastos: {e}"))
        
        def mostrar_datos_gastos(datos_gastos):
            # Quitar mensaje de carga
            loading_label.destroy()
            
            # Crear frame principal
            main_frame = tk.Frame(ventana_gastos, bg=self.controller.colores['claro']['panel'])
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Título
            tk.Label(
                main_frame,
                text="Lista de Gastos",
                font=("Comic Sans MS", 16, "bold"),
                fg=self.controller.colores['claro']['acento'],
                bg=self.controller.colores['claro']['panel']
            ).pack(anchor=tk.W, pady=(0, 10))
            
            # Frame para filtros
            filtros_frame = tk.Frame(main_frame, bg=self.controller.colores['claro']['panel'])
            filtros_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Instrucciones para selección múltiple
            instrucciones_label = tk.Label(
                main_frame,
                text="💡 Consejo: Selecciona gastos con Ctrl+Click (múltiple) o Shift+Click (rango)",
                font=("Comic Sans MS", 11),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel']
            )
            instrucciones_label.pack(anchor=tk.W, pady=(0, 10))
            
            # Crear el treeview para mostrar los datos
            columns = ("ID", "Nombre", "Monto", "Recurrente", "Fecha")
            
            # Frame para contener el treeview y scrollbar
            tree_frame = tk.Frame(main_frame, bg=self.controller.colores['claro']['panel'])
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(tree_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Treeview
            tree = ttk.Treeview(
                tree_frame,
                columns=columns,
                show="headings",
                yscrollcommand=scrollbar.set
            )
            scrollbar.config(command=tree.yview)
            
            # Configurar columnas
            tree.column("ID", width=50, anchor=tk.CENTER)
            tree.column("Nombre", width=250, anchor=tk.W)
            tree.column("Monto", width=100, anchor=tk.E)
            tree.column("Recurrente", width=100, anchor=tk.CENTER)
            tree.column("Fecha", width=100, anchor=tk.CENTER)
            
            # Configurar cabeceras
            tree.heading("ID", text="ID", anchor=tk.CENTER)
            tree.heading("Nombre", text="Nombre", anchor=tk.W)
            tree.heading("Monto", text="Monto", anchor=tk.E)
            tree.heading("Recurrente", text="Recurrente", anchor=tk.CENTER)
            tree.heading("Fecha", text="Fecha", anchor=tk.CENTER)
            
            # Insertar datos
            if datos_gastos:
                for gasto in datos_gastos:
                    try:
                        # Validar que tenga todos los campos necesarios
                        gasto_id = gasto[0] if len(gasto) > 0 else "N/A"
                        nombre = gasto[1] if len(gasto) > 1 else "N/A"
                        monto = f"${gasto[2]:.2f}" if len(gasto) > 2 and gasto[2] is not None else "N/A"
                        recurrente = "Sí" if len(gasto) > 3 and gasto[3] == 1 else "No"
                        fecha = gasto[4] if len(gasto) > 4 and gasto[4] else "N/A"
                        
                        tree.insert("", tk.END, values=(gasto_id, nombre, monto, recurrente, fecha))
                    except Exception as e:
                        logger.error(f"Error al insertar gasto en treeview: {e}")
            
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Frame para botones
            botones_frame = tk.Frame(main_frame, bg=self.controller.colores['claro']['panel'])
            botones_frame.pack(pady=(10, 0), anchor=tk.SE, fill=tk.X)
            
            # Botón de eliminar seleccionados
            def eliminar_seleccionados():
                seleccionados = tree.selection()
                if not seleccionados:
                    messagebox.showwarning("Atención", "Debes seleccionar al menos un gasto para eliminar.")
                    return
                
                cantidad = len(seleccionados)
                if messagebox.askyesno("Confirmar", f"¿Eliminar {cantidad} gasto(s) seleccionado(s)? Esta acción no se puede deshacer."):
                    try:
                        for item in seleccionados:
                            valores = tree.item(item)['values']
                            gasto_id = valores[0]
                            # Eliminar por ID
                            from src.models.data_manager import eliminar_dato
                            eliminar_dato('gastos', 'id', gasto_id)
                            tree.delete(item)
                        messagebox.showinfo("Éxito", f"{cantidad} gasto(s) eliminado(s).")
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al eliminar: {e}")
            
            tk.Button(
                botones_frame,
                text="🗑️ Eliminar Seleccionados",
                font=("Comic Sans MS", 12),
                bg=self.controller.colores['claro']['alerta'],
                fg="white",
                relief=tk.FLAT,
                padx=10,
                pady=5,
                command=eliminar_seleccionados,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)
            
            # Botón de cerrar
            tk.Button(
                botones_frame,
                text="Cerrar",
                font=("Comic Sans MS", 12),
                bg=self.controller.colores['claro']['borde'],
                fg=self.controller.colores['claro']['texto'],
                relief=tk.FLAT,
                padx=10,
                pady=5,
                command=ventana_gastos.destroy,
                cursor="hand2"
            ).pack(side=tk.RIGHT, padx=5)
        
        # Iniciar carga en un hilo separado
        threading.Thread(target=cargar_gastos_en_hilo, daemon=True).start()

    def mostrar_historial_gastos(self):
        """Muestra el historial de gastos"""
        messagebox.showinfo("Historial de Gastos", 
                            "La funcionalidad de historial de gastos está en desarrollo.\n\n"
                            "Estará disponible en la próxima actualización.")
    
    def agregar_gasto_event(self, event):
        """Método para manejar eventos de teclado cuando se presiona Enter"""
        self.agregar_gasto()
    
    def eliminar_gasto(self):
        """Elimina un gasto de la base de datos"""
        # Obtener el nombre del gasto a eliminar
        nombre = self.combo_gasto_nombre.get().strip()
        
        # Validar que el nombre no esté vacío
        if not nombre:
            messagebox.showerror("Error", "Debe ingresar el nombre del gasto a eliminar.")
            self.combo_gasto_nombre.focus_set()
            return
        
        # Confirmar eliminación
        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el gasto '{nombre}'?"
        )
        
        if confirmar:
            # Iniciar proceso de eliminación en un hilo separado
            threading.Thread(
                target=self._eliminar_gasto_hilo,
                args=(nombre,),
                daemon=True
            ).start()
            
            # Deshabilitar botones durante el proceso
            self.btn_eliminar_gasto.config(state="disabled", text="Eliminando...")
    
    def _eliminar_gasto_hilo(self, nombre):
        """Proceso de eliminación en un hilo separado"""
        try:
            resultado = eliminar_dato('gastos', 'nombre', nombre)
            
            # Actualizar UI en el hilo principal
            self.after(0, lambda: self._actualizar_ui_despues_eliminar(resultado, nombre))
        except Exception as e:
            logger.error(f"Error al eliminar gasto: {e}")
            self.after(0, lambda: self._actualizar_ui_despues_eliminar(False, nombre, str(e)))
    
    def _actualizar_ui_despues_eliminar(self, resultado, nombre, error_msg=None):
        """Actualiza la UI después de eliminar un gasto"""
        # Restaurar botón
        self.btn_eliminar_gasto.config(state="normal", text="❌ Eliminar")
        
        if resultado:
            messagebox.showinfo("Éxito", f"Gasto '{nombre}' eliminado correctamente.")
            
            # Limpiar los campos
            self.combo_gasto_nombre.set("")
            self.entry_gasto_monto.delete(0, tk.END)
            self.chk_var_recurrente.set(0)
            
            # Actualizar la lista de nombres en un hilo separado
            ThreadManager.create_thread(target=self._cargar_datos_en_hilo)
        else:
            if error_msg:
                messagebox.showerror("Error", f"Ocurrió un error al eliminar el gasto: {error_msg}")
            else:
                messagebox.showinfo("Información", f"No se encontró ningún gasto con el nombre '{nombre}'.")