# ui/dashboard_financiero.py
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('TkAgg')  # Importante para evitar problemas en algunos sistemas

from model.data_manager import cargar_datos
from model.ia_module import modulo_ia

class DashboardFinanciero(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.title("Dashboard Financiero IA")
        self.geometry("900x650")
        self.configure(bg=controller.colores['claro']['panel'])
        
        # Inicializar banderas de control
        self.interfaz_creada = False
        self.actualizando_interfaz = False
        
        # Permitir redimensionar la ventana
        self.resizable(True, True)
        
        # Permitir maximizar/minimizar
        self.minsize(600, 450)  # Tamaño mínimo
        
        # Centrar la ventana
        self.centrar_ventana()
        
        # Agregar botón de maximizar en la parte superior
        self.agregar_botones_ventana()
        
        # Hacer la ventana modal
        self.transient(parent)
        self.grab_set()
        
        # Inicializar datos
        self.cargar_datos()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Vincular evento de redimensionamiento
        self.bind("<Configure>", self.ajustar_interfaz)
    
    def cargar_datos(self):
        """Carga los datos necesarios para el dashboard"""
        try:
            # Obtener datos de gastos e ingresos usando la función importada
            self.gastos = cargar_datos("gastos")
            self.ingresos = cargar_datos("ingresos")
            
            # Si no hay datos, inicializar con listas vacías para evitar errores
            if self.gastos is None:
                self.gastos = []
            if self.ingresos is None:
                self.ingresos = []
                
            # Inicializar otras variables de datos que se usarán
            self.total_gastos = sum(gasto['monto'] for gasto in self.gastos) if self.gastos else 0
            self.total_ingresos = sum(ingreso['monto'] for ingreso in self.ingresos) if self.ingresos else 0
            self.balance = self.total_ingresos - self.total_gastos
            
        except Exception as e:
            print(f"Error al cargar datos para el dashboard: {e}")
            # Inicializar con valores predeterminados para evitar errores
            self.gastos = []
            self.ingresos = []
            self.total_gastos = 0
            self.total_ingresos = 0
            self.balance = 0
    
    def centrar_ventana(self):
        """Centra la ventana en la pantalla"""
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry('{}x{}+{}+{}'.format(ancho, alto, x, y))
    
    def agregar_botones_ventana(self):
        """Agrega botones para controlar la ventana"""
        botones_frame = tk.Frame(self, bg=self.controller.colores['claro']['panel'])
        botones_frame.pack(fill=tk.X, anchor='ne', padx=5, pady=5)
        
        # Botón de maximizar
        self.btn_maximizar = tk.Button(
            botones_frame,
            text="⬜",
            command=self.toggle_maximizar,
            font=("Comic Sans MS", 8),
            bg=self.controller.colores['claro']['acento_oscuro'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            width=2,
            height=1
        )
        self.btn_maximizar.pack(side=tk.RIGHT, padx=2)
        self.controller.redondear_widget(self.btn_maximizar)
        
        # Botón de cerrar
        btn_cerrar = tk.Button(
            botones_frame,
            text="✖",
            command=self.destroy,
            font=("Comic Sans MS", 8),
            bg=self.controller.colores['claro']['alerta'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            width=2,
            height=1
        )
        btn_cerrar.pack(side=tk.RIGHT, padx=2)
        self.controller.redondear_widget(btn_cerrar)
    
    def toggle_maximizar(self):
        """Alterna entre estado maximizado y normal"""
        if self.state() == 'zoomed':
            self.state('normal')
            self.btn_maximizar.config(text="⬜")
        else:
            self.state('zoomed')
            self.btn_maximizar.config(text="❐")
    
    def ajustar_interfaz(self, event=None):
        """Ajusta la interfaz cuando cambia el tamaño de la ventana"""
        # Evitar procesamiento durante actualización
        if hasattr(self, 'actualizando_interfaz') and self.actualizando_interfaz:
            return
            
        # Solo responder a cambios de tamaño de la ventana principal
        if event and event.widget != self:
            return
            
        self.actualizando_interfaz = True
        
        # Reconfigurar el tamaño de los gráficos según el nuevo tamaño de ventana
        if hasattr(self, 'grafico_frame'):
            # Actualizar los gráficos para que se ajusten al nuevo tamaño
            self.actualizar_graficos()
        
        self.actualizando_interfaz = False
    
    def crear_interfaz(self):
        """Crea la interfaz del dashboard"""
        # Evitar llamadas recursivas
        if hasattr(self, 'interfaz_creada') and self.interfaz_creada:
            return
            
        self.actualizando_interfaz = True
        
        # Frame principal con borde y padding
        self.main_frame = tk.Frame(
            self, 
            bg=self.controller.colores['claro']['panel'],
            padx=20, 
            pady=20
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título del dashboard
        tk.Label(
            self.main_frame,
            text="Dashboard Financiero Inteligente",
            font=("Comic Sans MS", 18, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 20))
        
        # Panel de selección de periodo
        periodo_frame = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        periodo_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            periodo_frame,
            text="Periodo:",
            font=("Comic Sans MS", 12),
            fg=self.controller.colores['claro']['texto'],
            bg=self.controller.colores['claro']['panel']
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Variable para el periodo seleccionado
        self.periodo_var = tk.StringVar(value="Último mes")
        
        # Lista de periodos disponibles
        periodos = ["Último mes", "Últimos 3 meses", "Último año", "Todo"]
        
        # Combobox para selección de periodo
        periodo_combo = ttk.Combobox(
            periodo_frame,
            textvariable=self.periodo_var,
            values=periodos,
            font=("Comic Sans MS", 10),
            state="readonly",
            width=15
        )
        periodo_combo.pack(side=tk.LEFT)
        
        # Vincular evento de cambio
        periodo_combo.bind("<<ComboboxSelected>>", self.actualizar_dashboard)
        
        # Panel de KPIs
        self.kpi_frame = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        self.kpi_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Panel de gráficos
        graficos_frame = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        graficos_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Gráfico izquierdo
        self.grafico_izquierdo = tk.Frame(
            graficos_frame,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10,
            highlightbackground=self.controller.colores['claro']['borde'],
            highlightthickness=1
        )
        self.grafico_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Gráfico derecho
        self.grafico_derecho = tk.Frame(
            graficos_frame,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10,
            highlightbackground=self.controller.colores['claro']['borde'],
            highlightthickness=1
        )
        self.grafico_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Panel inferior
        panel_inferior = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        panel_inferior.pack(fill=tk.X, pady=(0, 10))
        
        # Anomalías
        self.anomalias_frame = tk.Frame(
            panel_inferior,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10,
            highlightbackground=self.controller.colores['claro']['borde'],
            highlightthickness=1,
            width=300
        )
        self.anomalias_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Recomendaciones
        self.recomendaciones_frame = tk.Frame(
            panel_inferior,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10,
            highlightbackground=self.controller.colores['claro']['borde'],
            highlightthickness=1
        )
        self.recomendaciones_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Inicializar con datos actuales
        self.actualizar_dashboard()
        
        self.interfaz_creada = True
        self.actualizando_interfaz = False

    def actualizar_graficos(self):
        """Actualiza los gráficos para ajustarlos al nuevo tamaño"""
        # Evitar actualizaciones si estamos en proceso de actualización
        if self.actualizando_interfaz:
            return
            
        self.actualizando_interfaz = True
        
        # Actualizar dashboard completo
        self.actualizar_dashboard()
        
        self.actualizando_interfaz = False
    
    def crear_grafico_tendencia(self, ancho=400, alto=300):
        """Crea un gráfico de tendencia según el tamaño especificado"""
        # Implementación según las necesidades
        fig, ax = plt.subplots(figsize=(ancho/100, alto/100), dpi=100)
        # Configuración adicional del gráfico...
        return fig, ax
    
    def redondear_widget(self, widget):
        """Aplica estilo redondeado a los widgets"""
        try:
            widget.config(relief=tk.FLAT, borderwidth=0)
            if hasattr(widget, 'config') and callable(getattr(widget.config, '__call__', None)):
                widget.config(highlightthickness=0)
        except Exception as e:
            print(f"No se pudieron aplicar bordes redondeados: {e}")
    
    def actualizar_dashboard(self, event=None):
        """Actualiza todos los componentes del dashboard"""
        # Evitar actualizaciones si estamos en proceso de actualización
        if hasattr(self, 'actualizando_interfaz') and self.actualizando_interfaz:
            return
            
        # Verificar que todos los frames necesarios existen
        if not hasattr(self, 'kpi_frame') or not hasattr(self, 'grafico_izquierdo') or not hasattr(self, 'grafico_derecho'):
            return
            
        self.actualizando_interfaz = True
        
        # Filtrar datos según el periodo seleccionado
        periodo = self.periodo_var.get()
        fecha_inicio = None
        
        if periodo == "Último mes":
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        elif periodo == "Últimos 3 meses":
            fecha_inicio = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        elif periodo == "Último año":
            fecha_inicio = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Filtrar datos
        gastos_filtrados = self.gastos if fecha_inicio is None else [
            g for g in self.gastos if g['fecha'] >= fecha_inicio
        ]
        
        ingresos_filtrados = self.ingresos if fecha_inicio is None else [
            i for i in self.ingresos if i['fecha'] >= fecha_inicio
        ]
        
        # Actualizar componentes
        self.actualizar_kpis(gastos_filtrados, ingresos_filtrados)
        self.actualizar_grafico_izquierdo(gastos_filtrados)
        self.actualizar_grafico_derecho(gastos_filtrados, ingresos_filtrados)
        self.actualizar_anomalias(gastos_filtrados)
        self.actualizar_recomendaciones(gastos_filtrados, ingresos_filtrados)
        
        self.actualizando_interfaz = False
    
    def actualizar_kpis(self, gastos, ingresos):
        """Actualiza los KPIs financieros principales"""
        # Limpiar frame actual
        for widget in self.kpi_frame.winfo_children():
            widget.destroy()
        
        # Calcular KPIs
        total_gastos = sum(g['monto'] for g in gastos)
        total_ingresos = sum(i['monto'] for i in ingresos)
        balance = total_ingresos - total_gastos
        tasa_ahorro = (balance / total_ingresos * 100) if total_ingresos > 0 else 0
        
        # Crear tarjetas de KPI
        kpis = [
            {
                'titulo': 'Total Ingresos',
                'valor': f"${total_ingresos:.2f}",
                'color': self.controller.colores['claro']['exito'],
                'icono': '💰'
            },
            {
                'titulo': 'Total Gastos',
                'valor': f"${total_gastos:.2f}",
                'color': self.controller.colores['claro']['alerta'],
                'icono': '💸'
            },
            {
                'titulo': 'Balance',
                'valor': f"${balance:.2f}",
                'color': self.controller.colores['claro']['exito'] if balance >= 0 else self.controller.colores['claro']['alerta'],
                'icono': '⚖️'
            },
            {
                'titulo': 'Tasa de Ahorro',
                'valor': f"{tasa_ahorro:.1f}%",
                'color': self.controller.colores['claro']['exito'] if tasa_ahorro >= 20 else 
                         (self.controller.colores['claro']['destacado'] if tasa_ahorro > 0 else self.controller.colores['claro']['alerta']),
                'icono': '📊'
            }
        ]
        
        # Crear tarjetas visuales
        for i, kpi in enumerate(kpis):
            tarjeta = tk.Frame(
                self.kpi_frame,
                bg=self.controller.colores['claro']['panel'],
                highlightbackground=kpi['color'],
                highlightthickness=2,
                padx=15,
                pady=15
            )
            tarjeta.grid(row=0, column=i, padx=10, sticky='ew')
            
            # Configurar que la tarjeta se expanda
            self.kpi_frame.grid_columnconfigure(i, weight=1)
            
            # Icono
            tk.Label(
                tarjeta,
                text=kpi['icono'],
                font=("Comic Sans MS", 24),
                fg=kpi['color'],
                bg=self.controller.colores['claro']['panel']
            ).pack(anchor='w')
            
            # Valor
            tk.Label(
                tarjeta,
                text=kpi['valor'],
                font=("Comic Sans MS", 18, "bold"),
                fg=kpi['color'],
                bg=self.controller.colores['claro']['panel']
            ).pack(anchor='w')
            
            # Título
            tk.Label(
                tarjeta,
                text=kpi['titulo'],
                font=("Comic Sans MS", 12),
                fg=self.controller.colores['claro']['texto'],
                bg=self.controller.colores['claro']['panel']
            ).pack(anchor='w')
    
    def actualizar_grafico_izquierdo(self, gastos):
        """Actualiza el gráfico izquierdo (distribución de gastos por categoría)"""
        # Limpiar frame actual
        for widget in self.grafico_izquierdo.winfo_children():
            widget.destroy()
        
        # Título
        tk.Label(
            self.grafico_izquierdo,
            text="Distribución de Gastos por Categoría",
            font=("Comic Sans MS", 14, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 10))
        
        # Si no hay gastos, mostrar mensaje
        if not gastos:
            tk.Label(
                self.grafico_izquierdo,
                text="No hay datos de gastos en el periodo seleccionado",
                font=("Comic Sans MS", 12),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel']
            ).pack(pady=50)
            return
        
        # Crear figura y canvas
        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        
        # Agrupar por categoría
        categorias = {}
        for gasto in gastos:
            categoria = gasto.get('categoria', 'otros')
            if categoria not in categorias:
                categorias[categoria] = 0
            categorias[categoria] += gasto['monto']
        
        # Ordenar por valor (de mayor a menor)
        categorias_ordenadas = dict(sorted(categorias.items(), key=lambda x: x[1], reverse=True))
        
        # Colores personalizados
        colores = [
            '#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0', 
            '#ffb3e6', '#d9b38c', '#b3d9ff', '#ff6666', '#c2f0c2'
        ]
        
        # Crear gráfico de torta
        cuñas, textos, autotextos = ax.pie(
            categorias_ordenadas.values(), 
            labels=None,
            autopct='%1.1f%%',
            startangle=90,
            colors=colores[:len(categorias_ordenadas)]
        )
        
        # Personalizar textos
        plt.setp(autotextos, size=9, weight='bold')
        
        # Añadir leyenda
        ax.legend(
            cuñas, 
            categorias_ordenadas.keys(),
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )
        
        ax.set_title('Gastos por Categoría', fontsize=14)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        # Crear un contenedor para el gráfico que se ajuste
        canvas_frame = tk.Frame(self.grafico_izquierdo, bg=self.controller.colores['claro']['panel'])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Incrustar gráfico en Tkinter con opción de ajuste
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def actualizar_grafico_derecho(self, gastos, ingresos):
        """Actualiza el gráfico derecho (evolución de gastos e ingresos)"""
        # Limpiar frame actual
        for widget in self.grafico_derecho.winfo_children():
            widget.destroy()
        
        # Título
        tk.Label(
            self.grafico_derecho,
            text="Evolución Mensual de Gastos e Ingresos",
            font=("Comic Sans MS", 14, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 10))
        
        # Si no hay datos, mostrar mensaje
        if not gastos and not ingresos:
            tk.Label(
                self.grafico_derecho,
                text="No hay datos en el periodo seleccionado",
                font=("Comic Sans MS", 12),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel']
            ).pack(pady=50)
            return
        
        # Preparar datos para gráfico de barras
        # Agrupar por mes
        gastos_por_mes = {}
        ingresos_por_mes = {}
        
        # Función auxiliar para obtener clave de mes
        def obtener_clave_mes(fecha_str):
            try:
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                return fecha.strftime("%Y-%m")
            except:
                return "Sin fecha"
        
        # Procesar gastos
        for gasto in gastos:
            clave_mes = obtener_clave_mes(gasto['fecha'])
            if clave_mes not in gastos_por_mes:
                gastos_por_mes[clave_mes] = 0
            gastos_por_mes[clave_mes] += gasto['monto']
        
        # Procesar ingresos
        for ingreso in ingresos:
            clave_mes = obtener_clave_mes(ingreso['fecha'])
            if clave_mes not in ingresos_por_mes:
                ingresos_por_mes[clave_mes] = 0
            ingresos_por_mes[clave_mes] += ingreso['monto']
        
        # Obtener todos los meses únicos y ordenarlos
        todos_meses = sorted(set(list(gastos_por_mes.keys()) + list(ingresos_por_mes.keys())))
        
        # Limitar a los últimos 12 meses si hay muchos
        if len(todos_meses) > 12:
            todos_meses = todos_meses[-12:]
        
        # Crear listas ordenadas
        gastos_lista = [gastos_por_mes.get(mes, 0) for mes in todos_meses]
        ingresos_lista = [ingresos_por_mes.get(mes, 0) for mes in todos_meses]
        
        # Crear etiquetas más legibles
        etiquetas_meses = []
        for mes_clave in todos_meses:
            try:
                fecha = datetime.strptime(mes_clave, "%Y-%m")
                etiqueta = fecha.strftime("%b %y")  # Abreviatura del mes y año
                etiquetas_meses.append(etiqueta)
            except:
                etiquetas_meses.append(mes_clave)
        
        # Obtener dimensiones actuales del frame
        ancho_frame = self.grafico_derecho.winfo_width() or 400
        alto_frame = self.grafico_derecho.winfo_height() or 300
        
        # Ajustar tamaño del gráfico
        ancho_grafico = max(ancho_frame - 40, 300) / 100  # Convertir a pulgadas para figsize
        alto_grafico = max(alto_frame - 60, 200) / 100
        
        # Crear gráfico
        fig, ax = plt.subplots(figsize=(ancho_grafico, alto_grafico), dpi=100)
        
        # Configurar ancho de barras
        indice = np.arange(len(todos_meses))
        ancho = 0.35
        
        # Crear barras
        rects1 = ax.bar(indice - ancho/2, gastos_lista, ancho, label='Gastos', color=self.controller.colores['claro']['alerta'])
        rects2 = ax.bar(indice + ancho/2, ingresos_lista, ancho, label='Ingresos', color=self.controller.colores['claro']['exito'])
        
        # Añadir línea de balance
        balance_lista = [ingresos_lista[i] - gastos_lista[i] for i in range(len(ingresos_lista))]
        ax.plot(indice, balance_lista, 'o-', label='Balance', color=self.controller.colores['claro']['acento'])
        
        # Personalizar gráfico
        ax.set_xlabel('Mes')
        ax.set_ylabel('Monto ($)')
        ax.set_title('Gastos vs Ingresos por Mes')
        ax.set_xticks(indice)
        ax.set_xticklabels(etiquetas_meses, rotation=45)
        ax.legend()
        
        plt.tight_layout()
        
        # Crear un contenedor para el gráfico que se ajuste
        canvas_frame = tk.Frame(self.grafico_derecho, bg=self.controller.colores['claro']['panel'])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Incrustar gráfico en Tkinter con opción de ajuste
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def actualizar_anomalias(self, gastos):
        """Actualiza el panel de anomalías de gastos"""
        # Limpiar frame actual
        for widget in self.anomalias_frame.winfo_children():
            widget.destroy()
        
        # Título
        tk.Label(
            self.anomalias_frame,
            text="Detección de Gastos Anómalos",
            font=("Comic Sans MS", 14, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 10))
        
        # Detectar anomalías
        anomalias = modulo_ia.detectar_gastos_anomalos(gastos)
        
        if not anomalias:
            tk.Label(
                self.anomalias_frame,
                text="No se detectaron gastos anómalos en el periodo seleccionado.",
                font=("Comic Sans MS", 11),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel'],
                wraplength=300,
                justify='left'
            ).pack(anchor='w', pady=10)
            return
        
        # Mostrar hasta 5 anomalías principales
        anomalias = anomalias[:5] if len(anomalias) > 5 else anomalias
        
        # Crear tabla
        tabla_frame = tk.Frame(self.anomalias_frame, bg=self.controller.colores['claro']['panel'])
        tabla_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Cabecera de tabla
        columnas = ["Gasto", "Monto", "Desviación"]
        
        # Crear encabezados
        for i, columna in enumerate(columnas):
            tk.Label(
                tabla_frame,
                text=columna,
                font=("Comic Sans MS", 11, "bold"),
                fg=self.controller.colores['claro']['texto'],
                bg=self.controller.colores['claro']['borde']
            ).grid(row=0, column=i, sticky='ew', padx=1, pady=1)
        
        # Configurar columnas
        tabla_frame.grid_columnconfigure(0, weight=3)
        tabla_frame.grid_columnconfigure(1, weight=1)
        tabla_frame.grid_columnconfigure(2, weight=1)
        
        # Mostrar anomalías
        for i, anomalia in enumerate(anomalias, start=1):
            # Color de fondo alternado
            color_fondo = self.controller.colores['claro']['panel'] if i % 2 == 0 else self.controller.colores['claro']['fondo']
            
            # Nombre
            tk.Label(
                tabla_frame,
                text=anomalia['nombre'],
                font=("Comic Sans MS", 10),
                fg=self.controller.colores['claro']['texto'],
                bg=color_fondo,
                anchor='w',
                padx=5
            ).grid(row=i, column=0, sticky='ew', padx=1, pady=1)
            
            # Monto
            tk.Label(
                tabla_frame,
                text=f"${anomalia['monto']:.2f}",
                font=("Comic Sans MS", 10),
                fg=self.controller.colores['claro']['texto'],
                bg=color_fondo,
                anchor='e',
                padx=5
            ).grid(row=i, column=1, sticky='ew', padx=1, pady=1)
            
            # Desviación
            diferencia = anomalia.get('diferencia_porcentual', 0)
            tk.Label(
                tabla_frame,
                text=f"{diferencia:+.1f}%",
                font=("Comic Sans MS", 10, "bold"),
                fg=self.controller.colores['claro']['alerta'] if diferencia > 0 else self.controller.colores['claro']['exito'],
                bg=color_fondo,
                anchor='e',
                padx=5
            ).grid(row=i, column=2, sticky='ew', padx=1, pady=1)
    
    def actualizar_recomendaciones(self, gastos, ingresos):
        """Actualiza el panel de recomendaciones personalizadas"""
        # Limpiar frame actual
        for widget in self.recomendaciones_frame.winfo_children():
            widget.destroy()
        
        # Título
        tk.Label(
            self.recomendaciones_frame,
            text="Recomendaciones Personalizadas",
            font=("Comic Sans MS", 14, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 10))
        
        # Generar recomendaciones
        recomendaciones = modulo_ia.generar_recomendaciones(gastos, ingresos)
        
        # Mostrar recomendaciones
        contenedor_scroll = tk.Frame(self.recomendaciones_frame, bg=self.controller.colores['claro']['panel'])
        contenedor_scroll.pack(fill=tk.BOTH, expand=True)
        
        # Añadir canvas con scrollbar
        canvas = tk.Canvas(
            contenedor_scroll,
            bg=self.controller.colores['claro']['panel'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(contenedor_scroll, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.controller.colores['claro']['panel'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mostrar cada recomendación
        for i, recomendacion in enumerate(recomendaciones):
            # Crear frame para la recomendación
            rec_frame = tk.Frame(
                scrollable_frame,
                bg=self.controller.colores['claro']['panel'],
                highlightbackground=self.controller.colores['claro']['borde'],
                highlightthickness=1,
                padx=15,
                pady=15,
                bd=0
            )
            rec_frame.pack(fill=tk.X, pady=10)
            
            # Prioridad con ícono y color
            prioridad = recomendacion.get('prioridad', 'media')
            color_prioridad = {
                'alta': self.controller.colores['claro']['alerta'],
                'media': self.controller.colores['claro']['acento'],
                'baja': self.controller.colores['claro']['texto_suave']
            }.get(prioridad, self.controller.colores['claro']['texto'])
            
            icono_prioridad = {
                'alta': '🔴',
                'media': '🟠',
                'baja': '🟢'
            }.get(prioridad, '⚪')
            
            # Encabezado
            tk.Label(
                rec_frame,
                text=f"{icono_prioridad} {recomendacion.get('descripcion', 'Recomendación')}",
                font=("Comic Sans MS", 12, "bold"),
                fg=color_prioridad,
                bg=self.controller.colores['claro']['panel'],
                anchor='w'
            ).pack(fill=tk.X)
            
            # Detalle
            tk.Label(
                rec_frame,
                text=recomendacion.get('detalle', ''),
                font=("Comic Sans MS", 10),
                fg=self.controller.colores['claro']['texto'],
                bg=self.controller.colores['claro']['panel'],
                anchor='w',
                justify='left',
                wraplength=700
            ).pack(fill=tk.X, pady=5)
            
            # Impacto o ahorro potencial
            if 'impacto_estimado' in recomendacion:
                tk.Label(
                    rec_frame,
                    text=f"Impacto: {recomendacion['impacto_estimado']}",
                    font=("Comic Sans MS", 10, "italic"),
                    fg=self.controller.colores['claro']['texto_suave'],
                    bg=self.controller.colores['claro']['panel'],
                    anchor='w'
                ).pack(fill=tk.X)