import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import locale
import csv
import os
import calendar
from data_manager import (
    cargar_datos,
    guardar_ingreso,
    eliminar_dato,
    cargar_historial_conceptos,
    obtener_estadisticas_concepto,
)

class IngresosFrame(tk.Frame):
    def __init__(self, parent, controller):
        self.controller = controller
        colores = controller.colores['claro']
        
        # Crear un frame con borde y esquinas redondeadas (efecto panel)
        super().__init__(
            parent, 
            bg=colores['panel'],
            highlightbackground=colores['borde'],
            highlightthickness=1,
            padx=15, 
            pady=15,
            relief=tk.RAISED,
            bd=0
        )
        
        # Configurar locale para fechas en español argentino
        try:
            locale.setlocale(locale.LC_TIME, 'es_AR.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Alternativa
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_TIME, 'es.UTF-8')  # Más genérico
                except locale.Error:
                    print("No se pudo configurar el locale en español. Se usará el predeterminado.")
        
        # Crear widgets para ingresos
        self.crear_widgets()
        
    def crear_widgets(self):
        colores = self.controller.colores['claro']
        
        # Título de la sección con icono
        title_frame = tk.Frame(self, bg=colores['panel'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.label_ingreso = tk.Label(
            title_frame, 
            text="💵 Ingresos", 
            font=("Comic Sans MS", 14, "bold"), 
            fg=colores['texto'],
            bg=colores['panel']
        )
        self.label_ingreso.pack(anchor=tk.W)
        
        # Línea divisoria
        separator = ttk.Separator(title_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(5, 0))
        
        # Crear frame para formulario con margen
        form_frame = tk.Frame(self, bg=colores['panel'], pady=10)
        form_frame.pack(fill=tk.X)
        
        # Concepto del ingreso con historial
        self.label_ingreso_concepto = tk.Label(
            form_frame, 
            text="Concepto del ingreso:", 
            font=("Comic Sans MS", 10), 
            fg=colores['texto'],
            bg=colores['panel'],
            anchor=tk.W
        )
        self.label_ingreso_concepto.pack(fill=tk.X, pady=(10, 5))
        
        # Usar un combobox con mejor estilo para el historial
        self.conceptos_historicos = self.cargar_conceptos_historicos()
        self.combo_style = ttk.Style()
        self.combo_style.configure('TCombobox', padding=5)
        
        self.combo_ingreso_concepto = ttk.Combobox(
            form_frame, 
            values=self.conceptos_historicos, 
            font=("Comic Sans MS", 10),
            height=10,
            state="normal"
        )
        self.combo_ingreso_concepto.pack(fill=tk.X)
        
        # Monto del ingreso
        self.label_ingreso_monto = tk.Label(
            form_frame, 
            text="Monto del ingreso:", 
            font=("Comic Sans MS", 10), 
            fg=colores['texto'],
            bg=colores['panel'],
            anchor=tk.W
        )
        self.label_ingreso_monto.pack(fill=tk.X, pady=(10, 5))
        
        self.entry_ingreso_monto = tk.Entry(
            form_frame, 
            font=("Comic Sans MS", 10),
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1,
            highlightbackground=colores['borde']
        )
        self.entry_ingreso_monto.pack(fill=tk.X)
        
        # Fecha de ingreso (ahora con selector de fecha como en gastos)
        self.label_fecha_ingreso = tk.Label(
            form_frame, 
            text="Fecha del ingreso:", 
            font=("Comic Sans MS", 10), 
            fg=colores['texto'],
            bg=colores['panel'],
            anchor=tk.W
        )
        self.label_fecha_ingreso.pack(fill=tk.X, pady=(10, 5))
        
        # Frame para el selector de fecha
        fecha_frame = tk.Frame(form_frame, bg=colores['panel'])
        fecha_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Fecha por defecto
        fecha_prox_ingreso = self.controller.calcular_fecha_ingreso_semana_vencida()
        
        # Selector de fecha con formato argentino (dd/mm/yyyy)
        self.date_selector = DateEntry(
            fecha_frame,
            width=12,
            background=colores['acento'],
            foreground='white',
            borderwidth=2,
            year=fecha_prox_ingreso.year,
            month=fecha_prox_ingreso.month,
            day=fecha_prox_ingreso.day,
            font=("Comic Sans MS", 10),
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
        
        # Frame para botones
        buttons_frame = tk.Frame(self, bg=colores['panel'])
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Primera fila de botones
        top_buttons = tk.Frame(buttons_frame, bg=colores['panel'])
        top_buttons.pack(fill=tk.X, pady=(0, 5))
        
        # Botones de acción con íconos
        self.btn_agregar_ingreso = tk.Button(
            top_buttons, 
            text="➕ Agregar", 
            command=self.agregar_ingreso, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['exito'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_agregar_ingreso.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.round_button(self.btn_agregar_ingreso)
        
        self.btn_eliminar_ingreso = tk.Button(
            top_buttons, 
            text="❌ Eliminar", 
            command=self.eliminar_ingreso, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['alerta'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_eliminar_ingreso.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.round_button(self.btn_eliminar_ingreso)
        
        # Segunda fila de botones
        bottom_buttons = tk.Frame(buttons_frame, bg=colores['panel'])
        bottom_buttons.pack(fill=tk.X)
        
        self.btn_mostrar_ingresos = tk.Button(
            bottom_buttons, 
            text="📋 Mostrar Ingresos", 
            command=self.mostrar_ingresos, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['acento'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_mostrar_ingresos.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.round_button(self.btn_mostrar_ingresos)
        
        self.btn_historial_conceptos = tk.Button(
            bottom_buttons, 
            text="📊 Historial", 
            command=self.mostrar_historial_conceptos, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['destacado'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_historial_conceptos.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.round_button(self.btn_historial_conceptos)
        
        # Vincular la tecla Enter para agregar un ingreso
        self.entry_ingreso_monto.bind('<Return>', self.agregar_ingreso_event)
        
        # Vincular evento de selección del combobox
        self.combo_ingreso_concepto.bind('<<ComboboxSelected>>', self.concepto_seleccionado)
    
    def round_button(self, button):
        """Aplica estilo redondeado a los botones"""
        try:
            button.config(relief=tk.FLAT, borderwidth=0)
            # Intentar configuraciones adicionales para bordes redondeados
            if hasattr(button, 'config') and callable(getattr(button.config, '__call__', None)):
                button.config(highlightthickness=0)
        except Exception as e:
            print(f"No se pudieron aplicar bordes redondeados: {e}")
    
    def cargar_conceptos_historicos(self):
        """Carga el historial de conceptos de ingresos para el combobox"""
        try:
            # Obtener conceptos únicos de la base de datos
            conceptos = cargar_historial_conceptos()
            return conceptos if conceptos else []
        except Exception as e:
            print(f"Error al cargar conceptos históricos: {e}")
            return []
    
    def concepto_seleccionado(self, event):
        """Maneja la selección de un concepto desde el historial"""
        # Obtener el concepto seleccionado
        concepto = self.combo_ingreso_concepto.get()
        if not concepto:
            return
        
        # Obtener estadísticas del concepto
        try:
            estadisticas = obtener_estadisticas_concepto(concepto)
            if estadisticas['cantidad'] > 0:
                # Sugerir el monto promedio del concepto seleccionado
                self.entry_ingreso_monto.delete(0, tk.END)
                self.entry_ingreso_monto.insert(0, f"{estadisticas['promedio']:.2f}")
        except Exception as e:
            print(f"Error al obtener estadísticas del concepto: {e}")
    
    def agregar_ingreso_event(self, event):
        """Método para manejar eventos de teclado cuando se presiona Enter"""
        self.agregar_ingreso()
    
    def agregar_ingreso(self):
        """Agrega un nuevo ingreso a la base de datos"""
        # Obtener el modo actual para los colores
        modo = 'oscuro' if self.controller.modo_noche else 'claro'
        colores = self.controller.colores[modo]
        
        # Obtener valores de los campos
        concepto = self.combo_ingreso_concepto.get().strip()
        monto_str = self.entry_ingreso_monto.get().strip()
        
        # Validar que el concepto no esté vacío
        if not concepto:
            messagebox.showerror("Error", "Debe ingresar un concepto para el ingreso.")
            self.combo_ingreso_concepto.focus_set()
            return
        
        # Validar y convertir el monto
        try:
            monto = float(monto_str.replace(',', '.'))  # Reemplazar coma por punto para usuarios argentinos
            if monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor que cero.")
                self.entry_ingreso_monto.focus_set()
                return
        except ValueError:
            messagebox.showerror("Error", "Monto inválido. Por favor, ingrese un número válido.")
            self.entry_ingreso_monto.focus_set()
            return
        
        # Obtener la fecha seleccionada del DateEntry
        fecha_seleccionada = self.date_selector.get_date()
        fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
        
        # Guardar el ingreso en la base de datos
        try:
            if guardar_ingreso(concepto, monto, fecha_str):
                # Mostrar mensaje de éxito
                messagebox.showinfo(
                    "Ingreso Registrado", 
                    f"✅ El ingreso '{concepto}' de ${monto:.2f} ha sido registrado correctamente para la fecha {fecha_seleccionada.strftime('%d/%m/%Y')}."
                )
                
                # Limpiar los campos
                self.combo_ingreso_concepto.set("")
                self.entry_ingreso_monto.delete(0, tk.END)
                self.combo_ingreso_concepto.focus_set()
                
                # Actualizar la lista de conceptos históricos
                self.conceptos_historicos = self.cargar_conceptos_historicos()
                self.combo_ingreso_concepto['values'] = self.conceptos_historicos
            else:
                messagebox.showerror("Error", "No se pudo guardar el ingreso. Intente nuevamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al guardar el ingreso: {str(e)}")
            
    def eliminar_ingreso(self):
        """Elimina un ingreso de la base de datos"""
        # Obtener el concepto del ingreso a eliminar
        concepto = self.combo_ingreso_concepto.get().strip()
        
        # Validar que el concepto no esté vacío
        if not concepto:
            messagebox.showerror("Error", "Debe ingresar el concepto del ingreso a eliminar.")
            self.combo_ingreso_concepto.focus_set()
            return
        
        # Confirmar eliminación
        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el ingreso '{concepto}'?"
        )
        
        if confirmar:
            # Intentar eliminar el ingreso
            try:
                if eliminar_dato('ingresos', 'concepto', concepto):
                    messagebox.showinfo("Éxito", f"Ingreso '{concepto}' eliminado correctamente.")
                    
                    # Limpiar los campos
                    self.combo_ingreso_concepto.set("")
                    self.entry_ingreso_monto.delete(0, tk.END)
                    
                    # Actualizar la lista de conceptos históricos
                    self.conceptos_historicos = self.cargar_conceptos_historicos()
                    self.combo_ingreso_concepto['values'] = self.conceptos_historicos
                else:
                    messagebox.showinfo("Información", f"No se encontró ningún ingreso con el concepto '{concepto}'.")
            except Exception as e:
                messagebox.showerror("Error", f"Ocurrió un error al eliminar el ingreso: {str(e)}")
    
    def mostrar_ingresos(self):
        """Muestra todos los ingresos registrados en una ventana separada"""
        # Obtener el modo actual para los colores
        modo = 'oscuro' if self.controller.modo_noche else 'claro'
        colores = self.controller.colores[modo]
        
        # Cargar los datos de ingresos
        try:
            ingresos = cargar_datos('ingresos')
            
            if not ingresos:
                messagebox.showinfo("Ingresos", "No hay ingresos registrados.")
                return
            
            # Convertir las fechas para ordenamiento
            ingresos_con_fecha = []
            for ingreso in ingresos:
                id_ingreso, concepto, monto = ingreso[0], ingreso[1], ingreso[2]
                fecha_str = ingreso[3] if len(ingreso) > 3 and ingreso[3] else "1900-01-01"  # Fecha por defecto
                
                # Convertir la fecha string a objeto datetime para ordenamiento
                try:
                    fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
                except:
                    fecha_obj = datetime.strptime("1900-01-01", "%Y-%m-%d")  # Fecha mínima si hay error
                    
                # Solo incluir ingresos con monto > 0 (excluir registros de historial)
                if monto > 0:
                    ingresos_con_fecha.append((id_ingreso, concepto, monto, fecha_str, fecha_obj))
            
            # Ordenar por fecha (de más antiguo a más reciente)
            ingresos_ordenados = sorted(ingresos_con_fecha, key=lambda x: x[4])
            
            # Crear ventana para mostrar los ingresos
            ventana = tk.Toplevel(self.controller.root)
            ventana.title("Registro de Ingresos")
            ventana.geometry("700x500")
            ventana.configure(bg=colores['panel'])
            
            # Hacer la ventana modal
            ventana.transient(self.controller.root)
            ventana.grab_set()
            
            # Centrar la ventana
            ventana.update_idletasks()
            ancho = ventana.winfo_width()
            alto = ventana.winfo_height()
            x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
            y = (ventana.winfo_screenheight() // 2) - (alto // 2)
            ventana.geometry('{}x{}+{}+{}'.format(ancho, alto, x, y))
            
            # Título
            tk.Label(
                ventana, 
                text="📋 Registro de Ingresos", 
                font=("Comic Sans MS", 16, "bold"), 
                fg=colores['acento'],
                bg=colores['panel']
            ).pack(pady=(20, 10))
            
            # Frame para la tabla
            tabla_frame = tk.Frame(ventana, bg=colores['panel'], padx=20, pady=10)
            tabla_frame.pack(fill=tk.BOTH, expand=True)
            
            # Crear tabla con Treeview
            columnas = ("concepto", "monto", "fecha")
            tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=15)
            
            # Definir estilo para la tabla
            estilo = ttk.Style()
            estilo.configure("Treeview", font=("Comic Sans MS", 10))
            estilo.configure("Treeview.Heading", font=("Comic Sans MS", 10, "bold"))
            
            # Configurar encabezados
            tabla.heading("concepto", text="Concepto del Ingreso")
            tabla.heading("monto", text="Monto ($)")
            tabla.heading("fecha", text="Fecha")
            
            # Configurar columnas
            tabla.column("concepto", width=300, anchor=tk.W)
            tabla.column("monto", width=150, anchor=tk.E)
            tabla.column("fecha", width=150, anchor=tk.CENTER)
            
            # Agregar scrollbar
            scrollbar = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=tabla.yview)
            tabla.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Insertar datos ordenados por fecha
            total_ingresos = 0
            for ingreso in ingresos_ordenados:
                id_ingreso, concepto, monto, fecha_str = ingreso[0], ingreso[1], ingreso[2], ingreso[3]
                
                # Formatear la fecha al estilo argentino
                fecha_display = "No especificada"
                if fecha_str != "No especificada" and fecha_str != "1900-01-01":
                    try:
                        fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                        fecha_display = fecha_dt.strftime("%d/%m/%Y")
                    except:
                        fecha_display = fecha_str
                
                tabla.insert("", tk.END, values=(concepto, f"{monto:.2f}", fecha_display))
                total_ingresos += monto
            
            # Mostrar total
            total_frame = tk.Frame(ventana, bg=colores['panel'], padx=20, pady=10)
            total_frame.pack(fill=tk.X)
            
            tk.Label(
                total_frame, 
                text="Total Ingresos:", 
                font=("Comic Sans MS", 12, "bold"), 
                fg=colores['texto'],
                bg=colores['panel']
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            tk.Label(
                total_frame, 
                text=f"${total_ingresos:.2f}", 
                font=("Comic Sans MS", 12, "bold"), 
                fg=colores['exito'],
                bg=colores['panel']
            ).pack(side=tk.LEFT)
            
            # Botón de cerrar
            btn_cerrar = tk.Button(
                ventana, 
                text="Cerrar", 
                command=ventana.destroy, 
                font=("Comic Sans MS", 11), 
                bg=colores['acento'],
                fg="white",
                padx=15,
                pady=5,
                relief=tk.FLAT,
                cursor="hand2",
                borderwidth=0
            )
            btn_cerrar.pack(pady=(5, 20))
            self.round_button(btn_cerrar)
            
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al cargar los ingresos: {str(e)}")
    
    def mostrar_historial_conceptos(self):
        """
        Muestra el historial de conceptos de ingresos con información estadística detallada
        y opciones avanzadas de visualización y exportación.
        """
        try:
            # Obtener el modo actual para los colores
            modo = 'oscuro' if self.controller.modo_noche else 'claro'
            colores = self.controller.colores[modo]
            
            # Obtener datos históricos de conceptos
            conceptos_historial = cargar_historial_conceptos()
            
            if not conceptos_historial:
                messagebox.showinfo("Historial", "No hay datos históricos de ingresos.")
                return
            
            # Obtener datos reales de transacciones de ingresos
            ingresos_actuales = cargar_datos('ingresos', incluir_historial=True)  # Cargar todos los datos
            
            # Filtrar solo registros que no son historial
            ingresos_actuales = [ingreso for ingreso in ingresos_actuales if len(ingreso) > 4 and not ingreso[4] and ingreso[2] > 0]
            
            # Crear un diccionario para agrupar los ingresos por concepto
            historial = {}
            
            # Inicializar historial con todos los conceptos del historial
            for concepto in conceptos_historial:
                historial[concepto] = []
                
            # Agregar los ingresos actuales al historial
            for ingreso in ingresos_actuales:
                id_ingreso = ingreso[0]
                concepto = ingreso[1]
                monto = ingreso[2]
                fecha = ingreso[3] if len(ingreso) > 3 and ingreso[3] else "No especificada"
                
                if concepto in historial and monto > 0:  # Solo incluir transacciones reales
                    historial[concepto].append({
                        'id': id_ingreso,
                        'monto': monto,
                        'fecha': fecha
                    })
            
            # Crear ventana para mostrar el historial
            ventana = tk.Toplevel(self.controller.root)
            ventana.title("Historial Detallado de Ingresos")
            ventana.geometry("950x700")
            ventana.configure(bg=colores['panel'])
            
            # Hacer la ventana modal
            ventana.transient(self.controller.root)
            ventana.grab_set()
            
            # Centrar la ventana
            ventana.update_idletasks()
            ancho = ventana.winfo_width()
            alto = ventana.winfo_height()
            x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
            y = (ventana.winfo_screenheight() // 2) - (alto // 2)
            ventana.geometry('{}x{}+{}+{}'.format(ancho, alto, x, y))
            
            # Crear un frame principal con padding
            main_frame = tk.Frame(ventana, bg=colores['panel'], padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Título con contador de categorías
            titulo_frame = tk.Frame(main_frame, bg=colores['panel'])
            titulo_frame.pack(fill=tk.X, pady=(0, 15))
            
            tk.Label(
                titulo_frame, 
                text=f"📊 Historial de Ingresos ({len(conceptos_historial)} conceptos)", 
                font=("Comic Sans MS", 18, "bold"), 
                fg=colores['acento'],
                bg=colores['panel']
            ).pack(side=tk.LEFT, pady=(5, 10))
            
            # Frame para opciones de filtro
            filtro_frame = tk.Frame(main_frame, bg=colores['panel'], pady=10)
            filtro_frame.pack(fill=tk.X, pady=(0, 15))
            
            # Etiqueta para el filtro
            tk.Label(
                filtro_frame, 
                text="Filtrar por:", 
                font=("Comic Sans MS", 10, "bold"), 
                fg=colores['texto'],
                bg=colores['panel']
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            # Variable para almacenar el valor del filtro
            self.filtro_var = tk.StringVar(value="Todos")
            
            # Opciones de filtro
            opciones = ["Todos", "Últimos 30 días", "Este mes", "Este año", "Montos > $1000", "Montos < $1000"]
            
            # Combobox para el filtro
            combo_filtro = ttk.Combobox(
                filtro_frame, 
                values=opciones,
                textvariable=self.filtro_var,
                font=("Comic Sans MS", 10),
                width=15,
                state="readonly"
            )
            combo_filtro.pack(side=tk.LEFT, padx=(0, 20))
            
            # Etiqueta para búsqueda
            tk.Label(
                filtro_frame, 
                text="Buscar:", 
                font=("Comic Sans MS", 10, "bold"), 
                fg=colores['texto'],
                bg=colores['panel']
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            # Variable para la búsqueda
            self.busqueda_var = tk.StringVar()
            
            # Entrada para búsqueda
            entry_busqueda = tk.Entry(
                filtro_frame,
                textvariable=self.busqueda_var,
                font=("Comic Sans MS", 10),
                width=20,
                bd=1,
                relief=tk.SOLID
            )
            entry_busqueda.pack(side=tk.LEFT, padx=(0, 10))
            
            # Botón de búsqueda
            btn_buscar = tk.Button(
                filtro_frame,
                text="🔍 Buscar",
                font=("Comic Sans MS", 9),
                bg=colores['acento'],
                fg="white",
                padx=10,
                pady=2,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda: aplicar_filtros()
            )
            btn_buscar.pack(side=tk.LEFT)
            
            # Botón de exportar a CSV
            btn_exportar = tk.Button(
                filtro_frame,
                text="📋 Exportar Datos",
                font=("Comic Sans MS", 9),
                bg=colores['destacado'],
                fg="white",
                padx=10,
                pady=2,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda: exportar_datos_csv()
            )
            btn_exportar.pack(side=tk.RIGHT)
            
            # Crear un notebook para las pestañas (una por concepto)
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Diccionario para almacenar referencias a los widgets
            pestanas = {}
            tablas = {}
            
            # Calcular total global de ingresos
            total_global = sum(sum(ingreso['monto'] for ingreso in ingresos) for ingresos in historial.values() if ingresos)
            
            # Frame para mostrar totales globales
            totales_frame = tk.Frame(main_frame, bg=colores['panel'], pady=10)
            totales_frame.pack(fill=tk.X, pady=10)
            
            tk.Label(
                totales_frame,
                text="Total de Ingresos:",
                font=("Comic Sans MS", 12, "bold"),
                fg=colores['texto'],
                bg=colores['panel']
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            total_label = tk.Label(
                totales_frame,
                text=f"${total_global:.2f}",
                font=("Comic Sans MS", 12, "bold"),
                fg=colores['exito'],
                bg=colores['panel']
            )
            total_label.pack(side=tk.LEFT)
            
            # Crear una pestaña para cada concepto
            for concepto, registros in historial.items():
                # Crear un frame para este concepto
                tab_frame = tk.Frame(notebook, bg=colores['panel'], padx=15, pady=15)
                pestanas[concepto] = tab_frame
                
                # Ordenar registros por fecha (más reciente primero)
                registros.sort(key=lambda x: x['fecha'] if x['fecha'] != "No especificada" else "0000-00-00", reverse=True)
                
                # Obtener estadísticas
                estadisticas = obtener_estadisticas_concepto(concepto)
                
                # Añadir la pestaña al notebook con ícono
                notebook.add(tab_frame, text=f"💵 {concepto}")
                
                # Verificar si hay datos para este concepto
                if not registros:
                    # Mostrar mensaje informativo si no hay datos
                    mensaje_frame = tk.Frame(tab_frame, bg=colores['panel'], padx=20, pady=20)
                    mensaje_frame.pack(fill=tk.BOTH, expand=True)
                    
                    # Ícono
                    tk.Label(
                        mensaje_frame,
                        text="💵",
                        font=("Comic Sans MS", 40),
                        fg=colores['acento'],
                        bg=colores['panel']
                    ).pack(pady=(30, 10))
                    
                    # Mensaje principal
                    tk.Label(
                        mensaje_frame,
                        text=f"No hay ingresos de '{concepto}' registrados",
                        font=("Comic Sans MS", 14, "bold"),
                        fg=colores['texto'],
                        bg=colores['panel']
                    ).pack(pady=(10, 5))
                    
                    # Información adicional
                    tk.Label(
                        mensaje_frame,
                        text="Podrás ver las estadísticas cuando registres ingresos con este concepto",
                        font=("Comic Sans MS", 12),
                        fg=colores['texto_suave'],
                        bg=colores['panel']
                    ).pack(pady=(0, 30))
                    
                    continue
                
                # Panel de resumen para este concepto
                resumen_frame = tk.Frame(tab_frame, bg=colores['panel'], padx=10, pady=10)
                resumen_frame.pack(fill=tk.X, pady=(0, 15))
                
                # Mostrar estadísticas en una cuadrícula
                estilo_etiqueta = {"font": ("Comic Sans MS", 10, "bold"), "bg": colores['panel'], "fg": colores['texto']}
                estilo_valor = {"font": ("Comic Sans MS", 10), "bg": colores['panel'], "fg": colores['acento']}
                
                # Primera fila
                tk.Label(resumen_frame, text="Total:", **estilo_etiqueta).grid(row=0, column=0, sticky=tk.W, pady=5)
                tk.Label(resumen_frame, text=f"${estadisticas['total']:.2f}", **estilo_valor).grid(row=0, column=1, sticky=tk.W, pady=5)
                
                tk.Label(resumen_frame, text="Promedio:", **estilo_etiqueta).grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
                tk.Label(resumen_frame, text=f"${estadisticas['promedio']:.2f}", **estilo_valor).grid(row=0, column=3, sticky=tk.W, pady=5)
                
                # Segunda fila
                tk.Label(resumen_frame, text="Mínimo:", **estilo_etiqueta).grid(row=1, column=0, sticky=tk.W, pady=5)
                tk.Label(resumen_frame, text=f"${estadisticas['minimo']:.2f}", **estilo_valor).grid(row=1, column=1, sticky=tk.W, pady=5)
                
                tk.Label(resumen_frame, text="Máximo:", **estilo_etiqueta).grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 0))
                tk.Label(resumen_frame, text=f"${estadisticas['maximo']:.2f}", **estilo_valor).grid(row=1, column=3, sticky=tk.W, pady=5)
                
                # Tercera fila
                tk.Label(resumen_frame, text="Cantidad:", **estilo_etiqueta).grid(row=2, column=0, sticky=tk.W, pady=5)
                tk.Label(resumen_frame, text=f"{estadisticas['cantidad']}", **estilo_valor).grid(row=2, column=1, sticky=tk.W, pady=5)
                
                # Porcentaje del total
                porcentaje = (estadisticas['total'] / total_global * 100) if total_global > 0 else 0
                tk.Label(resumen_frame, text="% del Total:", **estilo_etiqueta).grid(row=2, column=2, sticky=tk.W, pady=5, padx=(20, 0))
                tk.Label(resumen_frame, text=f"{porcentaje:.2f}%", **estilo_valor).grid(row=2, column=3, sticky=tk.W, pady=5)
                
                # Calcular última fecha
                ultima_fecha = "No disponible"
                if registros:
                    try:
                        ultima_fecha_str = max(r['fecha'] for r in registros if r['fecha'] != "No especificada" and r['fecha'])
                        ultima_fecha_obj = datetime.strptime(ultima_fecha_str, "%Y-%m-%d")
                        ultima_fecha = ultima_fecha_obj.strftime("%d/%m/%Y")
                    except (ValueError, TypeError):
                        ultima_fecha = "Formato incorrecto"
                
                tk.Label(resumen_frame, text="Último ingreso:", **estilo_etiqueta).grid(row=3, column=0, sticky=tk.W, pady=5)
                tk.Label(resumen_frame, text=ultima_fecha, **estilo_valor).grid(row=3, column=1, sticky=tk.W, pady=5)
                
                # Indicación gráfica de la proporción respecto al total
                barra_frame = tk.Frame(tab_frame, bg=colores['panel'], padx=10, pady=5)
                barra_frame.pack(fill=tk.X, pady=(0, 10))
                
                tk.Label(
                    barra_frame,
                    text="Proporción del ingreso total:",
                    font=("Comic Sans MS", 10, "bold"),
                    fg=colores['texto'],
                    bg=colores['panel']
                ).pack(anchor=tk.W, pady=(0, 5))
                
                # Canvas para la barra de proporción
                barra_canvas = tk.Canvas(
                    barra_frame,
                    width=600,
                    height=20,
                    bg=colores['borde'],
                    highlightthickness=0
                )
                barra_canvas.pack(fill=tk.X, pady=(0, 10))
                
                # Dibujar la barra
                ancho_proporcional = int(600 * porcentaje / 100) if porcentaje > 0 else 1
                barra_canvas.create_rectangle(
                    0, 0, ancho_proporcional, 20,
                    fill=colores['exito'],  # Verde para ingresos
                    outline=""
                )
                
                # Etiqueta con el porcentaje sobre la barra
                barra_canvas.create_text(
                    ancho_proporcional / 2, 10,
                    text=f"{porcentaje:.2f}%",
                    fill="white",
                    font=("Comic Sans MS", 8, "bold")
                )
                
                # Separador
                ttk.Separator(tab_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
                
                # Tabla de registros para este concepto
                tabla_frame = tk.Frame(tab_frame, bg=colores['panel'])
                tabla_frame.pack(fill=tk.BOTH, expand=True)
                
                # Crear tabla
                columnas = ("fecha", "monto")
                tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=12)
                tablas[concepto] = tabla
                
                # Configurar encabezados
                tabla.heading("fecha", text="Fecha", command=lambda: treeview_sort_column(tabla, "fecha", False))
                tabla.heading("monto", text="Monto ($)", command=lambda: treeview_sort_column(tabla, "monto", False))
                
                # Configurar columnas
                tabla.column("fecha", width=150, anchor=tk.CENTER)
                tabla.column("monto", width=150, anchor=tk.E)
                
                # Agregar scrollbar
                scrollbar = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=tabla.yview)
                tabla.configure(yscrollcommand=scrollbar.set)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                
                # Insertar cada registro
                for i, registro in enumerate(registros):
                    monto = registro['monto']
                    fecha_str = registro['fecha']
                    
                    # Formatear la fecha
                    fecha_formateada = fecha_str
                    if fecha_str != "No especificada":
                        try:
                            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                            fecha_formateada = fecha_dt.strftime("%d/%m/%Y")
                        except (ValueError, TypeError):
                            fecha_formateada = fecha_str
                    
                    # Insertar en la tabla
                    item = tabla.insert("", tk.END, values=(fecha_formateada, f"{monto:.2f}"))
                    
                    # Aplicar estilo de fila alterna
                    if i % 2 == 0:
                        tabla.item(item, tags=('even',))
                    else:
                        tabla.item(item, tags=('odd',))
                
                # Configurar estilos de filas
                tabla.tag_configure('even', background=colores['panel'])
                tabla.tag_configure('odd', background=colores['borde'])
            
            # Función para ordenar la tabla
            def treeview_sort_column(tv, col, reverse):
                l = [(tv.set(k, col), k) for k in tv.get_children('')]
                
                # Convertir a número si es la columna de monto
                if col == 'monto':
                    l = [(float(v.replace('$', '').strip()), k) for v, k in l]
                
                l.sort(reverse=reverse)
                
                # Reordenar los elementos
                for index, (val, k) in enumerate(l):
                    tv.move(k, '', index)
                    
                    # Actualizar estilos de filas alternadas
                    if index % 2 == 0:
                        tv.item(k, tags=('even',))
                    else:
                        tv.item(k, tags=('odd',))
                
                # Cambiar dirección de ordenamiento para el próximo clic
                tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))
            
            # Función para aplicar filtros a todas las pestañas
            def aplicar_filtros():
                filtro = self.filtro_var.get()
                busqueda = self.busqueda_var.get().lower().strip()
                
                # Obtener fecha actual para filtros temporales
                fecha_actual = datetime.now()
                primer_dia_mes = datetime(fecha_actual.year, fecha_actual.month, 1).strftime("%Y-%m-%d")
                primer_dia_anio = datetime(fecha_actual.year, 1, 1).strftime("%Y-%m-%d")
                
                # Fecha de 30 días atrás
                fecha_30_dias = (fecha_actual - timedelta(days=30)).strftime("%Y-%m-%d")
                
                # Recorrer todas las pestañas y tablas
                for concepto, tabla in tablas.items():
                    # Limpiar tabla
                    for item in tabla.get_children():
                        tabla.delete(item)
                    
                    # Filtrar registros según criterios
                    registros_filtrados = []
                    for registro in historial[concepto]:
                        # Aplicar filtro de fecha para "Últimos 30 días"
                        if filtro == "Últimos 30 días":
                            fecha_registro = registro['fecha']
                            if fecha_registro == "No especificada" or fecha_registro < fecha_30_dias:
                                continue
                        
                        # Aplicar filtro de fecha para "Este mes"
                        elif filtro == "Este mes":
                            fecha_registro = registro['fecha']
                            if fecha_registro == "No especificada" or fecha_registro < primer_dia_mes:
                                continue
                        
                        # Aplicar filtro de fecha para "Este año"
                        elif filtro == "Este año":
                            fecha_registro = registro['fecha']
                            if fecha_registro == "No especificada" or fecha_registro < primer_dia_anio:
                                continue
                        
                        # Aplicar filtro de monto para "> $1000"
                        elif filtro == "Montos > $1000":
                            if registro['monto'] <= 1000:
                                continue
                        
                        # Aplicar filtro de monto para "< $1000"
                        elif filtro == "Montos < $1000":
                            if registro['monto'] >= 1000:
                                continue
                        
                        # Aplicar filtro de búsqueda
                        if busqueda and busqueda not in concepto.lower():
                            continue
                        
                        registros_filtrados.append(registro)
                    
                    # Reinsertar los registros filtrados
                    for i, registro in enumerate(registros_filtrados):
                        monto = registro['monto']
                        fecha_str = registro['fecha']
                        
                        # Formatear la fecha
                        fecha_formateada = fecha_str
                        if fecha_str != "No especificada":
                            try:
                                fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                                fecha_formateada = fecha_dt.strftime("%d/%m/%Y")
                            except (ValueError, TypeError):
                                fecha_formateada = fecha_str
                        
                        # Insertar en la tabla
                        item = tabla.insert("", tk.END, values=(fecha_formateada, f"{monto:.2f}"))
                        
                        # Aplicar estilo de fila alterna
                        if i % 2 == 0:
                            tabla.item(item, tags=('even',))
                        else:
                            tabla.item(item, tags=('odd',))
                    
                    # Ocultar pestañas sin datos
                    if not registros_filtrados:
                        notebook.tab(pestanas[concepto], state='hidden')
                    else:
                        notebook.tab(pestanas[concepto], state='normal')
                
                # Actualizar total basado en registros filtrados
                total_filtrado = 0
                for concepto, tabla in tablas.items():
                    for item in tabla.get_children():
                        monto_str = tabla.item(item, 'values')[1]
                        try:
                            monto = float(monto_str.replace('$', '').strip())
                            total_filtrado += monto
                        except (ValueError, TypeError):
                            pass
                
                # Actualizar etiqueta de total
                total_label.config(text=f"${total_filtrado:.2f}")
                
                # Si no hay pestañas visibles, mostrar mensaje
                pestanas_visibles = [i for i, concepto in enumerate(historial.keys()) 
                                  if notebook.tab(i, 'state') != 'hidden']
                
                if not pestanas_visibles:
                    messagebox.showinfo("Filtro", "No hay ingresos que coincidan con el criterio de filtrado.")
            
            # Función para exportar datos a CSV
            def exportar_datos_csv():
                try:
                    # Solicitar ubicación para guardar el archivo
                    filename = filedialog.asksaveasfilename(
                        defaultextension=".csv",
                        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                        title="Guardar datos como CSV"
                    )
                    
                    if not filename:  # El usuario canceló
                        return
                    
                    # Filtros actuales
                    filtro = self.filtro_var.get()
                    busqueda = self.busqueda_var.get().lower().strip()
                    
                    # Crear archivo CSV
                    with open(filename, mode='w', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        
                        # Escribir encabezados
                        writer.writerow(["Concepto", "Fecha", "Monto"])
                        
                        # Escribir datos de todas las pestañas visibles
                        for i, (concepto, tabla) in enumerate(tablas.items()):
                            if notebook.tab(i, 'state') != 'hidden':
                                for item in tabla.get_children():
                                    valores = tabla.item(item, 'values')
                                    # Convertir fecha a formato ISO para Excel
                                    fecha_str = valores[0]
                                    try:
                                        fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
                                        fecha_iso = fecha_obj.strftime("%Y-%m-%d")
                                    except (ValueError, TypeError):
                                        fecha_iso = fecha_str
                                    
                                    # Limpiar monto
                                    monto_str = valores[1].replace('$', '').strip()
                                    
                                    # Escribir fila
                                    writer.writerow([
                                        concepto,
                                        fecha_iso,
                                        monto_str
                                    ])
                    
                    messagebox.showinfo("Exportación Exitosa", 
                        f"Los datos se han exportado correctamente a:\n{filename}")
                except Exception as e:
                    messagebox.showerror("Error", f"Ocurrió un error al exportar los datos: {str(e)}")
            
            # Botón de cerrar
            btn_cerrar = tk.Button(
                main_frame, 
                text="Cerrar", 
                command=ventana.destroy, 
                font=("Comic Sans MS", 11), 
                bg=colores['acento'],
                fg="white",
                padx=15,
                pady=5,
                relief=tk.FLAT,
                cursor="hand2",
                borderwidth=0
            )
            btn_cerrar.pack(pady=(5, 0))
            self.round_button(btn_cerrar)
            
            # Asignar acciones a eventos
            combo_filtro.bind("<<ComboboxSelected>>", lambda event: aplicar_filtros())
            entry_busqueda.bind("<Return>", lambda event: aplicar_filtros())
            
            # Configurar que al cambiar de pestaña se actualice el filtro
            notebook.bind("<<NotebookTabChanged>>", lambda event: aplicar_filtros())
                
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al mostrar el historial: {str(e)}")
    
    def actualizar_modo(self, modo):
        """Actualiza los colores del frame según el modo (claro/oscuro)"""
        colores = self.controller.colores[modo]
        
        # Actualizar el frame principal
        self.config(bg=colores['panel'], highlightbackground=colores['borde'])
        
        # Función recursiva para actualizar widgets
        def actualizar_widget(widget, colores):
            widget_class = widget.__class__.__name__
            
            # Saltar widgets de tipo Calendar y derivados - estos causan el error
            if "Calendar" in widget_class:
                return
                
            if isinstance(widget, tk.Label):
                widget.config(bg=colores['panel'], fg=colores['texto'])
                # Si es un título, usar color de acento
                if hasattr(widget, 'cget') and "bold" in widget.cget("font"):
                    widget.config(fg=colores['acento'])
            
            elif isinstance(widget, tk.Frame):
                widget.config(bg=colores['panel'])
                
            elif isinstance(widget, tk.Entry):
                widget.config(highlightbackground=colores['borde'])
            
            elif isinstance(widget, ttk.Separator):
                # Los separadores ttk se manejan a través de estilos
                pass
                
            # Manejo especial para DateEntry (calendario)
            elif isinstance(widget, DateEntry):
                try:
                    # Solo configurar propiedades seguras
                    widget.config(
                        background=colores['acento'],
                        foreground='white'
                    )
                except Exception as e:
                    print(f"Error al configurar DateEntry: {e}")
                    pass  # Ignorar errores en configuración
            
            # Recursivamente actualizar todos los widgets hijos
            for child in widget.winfo_children():
                actualizar_widget(child, colores)
        
        # Actualizar todos los widgets del frame
        actualizar_widget(self, colores)
        
        # Actualizar botones específicamente (mantener sus colores especiales)
        if hasattr(self, 'btn_agregar_ingreso'):
            self.btn_agregar_ingreso.config(bg=colores['exito'], fg="white")
        
        if hasattr(self, 'btn_eliminar_ingreso'):
            self.btn_eliminar_ingreso.config(bg=colores['alerta'], fg="white")
            
        if hasattr(self, 'btn_mostrar_ingresos'):
            self.btn_mostrar_ingresos.config(bg=colores['acento'], fg="white")
            
        if hasattr(self, 'btn_historial_conceptos'):
            self.btn_historial_conceptos.config(bg=colores['destacado'], fg="white")