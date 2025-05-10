# ui/dashboard_financiero.py
import sys
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
import matplotlib
import gc
import weakref
import threading
import logging

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='dashboard.log'
)
logger = logging.getLogger('dashboard_financiero')

matplotlib.use('TkAgg')  # Importante para evitar problemas en algunos sistemas

from model.data_manager import cargar_datos
from model.ia_module import modulo_ia

# Lista global para mantener referencia a figuras y prevenir recolección de basura prematura
_figuras_activas = []

def limpiar_figuras_inactivas():
    """Limpia referencias a figuras que ya no están en pantalla"""
    global _figuras_activas
    _figuras_activas = [fig for fig in _figuras_activas if fig() is not None]
    
class DashboardFinanciero(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.title("Dashboard Financiero IA")
        
        # Configurar para comportamiento nativo de ventana
        self.resizable(True, True)
        self.attributes('-alpha', 0.0)  # Ocultar temporalmente
        
        # Establecer como ventana normal, no de utilidad
        if hasattr(self, 'attributes'):
            self.attributes('-toolwindow', False)
        
        # Configurar tamaño y propiedades
        # Funciona en Windows
        self.state('zoomed')
        self.configure(bg=controller.colores['claro']['panel'])
        self.minsize(1280, 920)
        
        # Vincular doble clic en la barra de título para maximizar
        self.bind('<Double-Button-1>', self._toggle_maximize)
        
        # Inicializar datos
        self.interfaz_creada = False
        self.actualizando_interfaz = False
        self.figuras = []  # Para guardar referencias a los gráficos
        
        # Vincular evento de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Cargar datos en un hilo separado
        self.carga_exitosa = threading.Event()
        threading.Thread(target=self.cargar_datos_en_hilo, daemon=True).start()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Centrar la ventana
        self.centrar_ventana()
        
        # Hacer la ventana modal
        self.transient(parent)
        self.grab_set()
        
        # Vincular evento de redimensionamiento
        self.bind("<Configure>", self.ajustar_interfaz)
        
        # Mostrar la ventana con fade-in y forzar actualización inicial
        self.after(100, lambda: self.attributes('-alpha', 1.0))
        self.after(200, self.verificar_carga_datos)
    
    def verificar_carga_datos(self):
        """Verifica si los datos se han cargado y actualiza el dashboard"""
        if self.carga_exitosa.is_set():
            self.actualizar_dashboard()
        else:
            # Verificar nuevamente después de 100ms
            self.after(100, self.verificar_carga_datos)
    
    def cargar_datos_en_hilo(self):
        """Carga los datos en un hilo separado para no bloquear la UI"""
        try:
            logger.info("Iniciando carga de datos para el dashboard")
            # Obtener datos de gastos e ingresos
            self.gastos = cargar_datos("gastos")
            self.ingresos = cargar_datos("ingresos")
            
            # Inicializar otras variables de datos
            self.total_gastos = sum(gasto[2] for gasto in self.gastos if gasto[2] is not None and isinstance(gasto[2], (int, float)) and gasto[2] > 0)
            self.total_ingresos = sum(ingreso[2] for ingreso in self.ingresos if ingreso[2] is not None and isinstance(ingreso[2], (int, float)) and ingreso[2] > 0)
            self.balance = self.total_ingresos - self.total_gastos
            
            # Marcar que la carga de datos ha terminado
            self.carga_exitosa.set()
            logger.info(f"Datos cargados exitosamente: {len(self.gastos)} gastos, {len(self.ingresos)} ingresos")
        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")
            # Inicializar con valores predeterminados para evitar errores
            self.gastos = []
            self.ingresos = []
            self.total_gastos = 0
            self.total_ingresos = 0
            self.balance = 0
            
            # Marcar carga completada para no bloquear la UI
            self.carga_exitosa.set()
    
    def on_closing(self):
        """Maneja el cierre de la ventana, limpiando recursos"""
        # Liberar recursos de matplotlib
        self.limpiar_recursos_matplotlib()
        self.destroy()
    
    def limpiar_recursos_matplotlib(self):
        """Libera los recursos de matplotlib para evitar fugas de memoria"""
        try:
            # Limpiar referencias a figuras
            if hasattr(self, 'figuras'):
                for fig_weak in self.figuras:
                    fig = fig_weak()
                    if fig is not None:
                        plt.close(fig)
                self.figuras = []
            
            # Limpiar figuras globales
            global _figuras_activas
            for fig_weak in _figuras_activas:
                fig = fig_weak()
                if fig is not None:
                    plt.close(fig)
            _figuras_activas = []
            
            # Forzar recolección de basura
            gc.collect()
            logger.info("Recursos de matplotlib liberados")
        except Exception as e:
            logger.error(f"Error al limpiar recursos de matplotlib: {e}")
    
    def _toggle_maximize(self, event=None):
        """Alterna entre estado normal y maximizado con doble clic"""
        # Solo procesar eventos en la barra de título
        if event and event.y > 30:  # Aproximadamente el tamaño de una barra de título
            return
            
        if self.state() == 'zoomed':
            self.state('normal')
        else:
            self.state('zoomed')
        
        return "break"  # Prevenir propagación del evento
    
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
    
    def centrar_ventana(self):
        """Centra la ventana en la pantalla"""
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry('{}x{}+{}+{}'.format(ancho, alto, x, y))
        
        # Mostrar la ventana una vez configurada
        self.deiconify()
    
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
        
        # Mostrar mensaje de carga
        self.mensaje_carga = tk.Label(
            self.main_frame,
            text="Cargando datos...",
            font=("Comic Sans MS", 14),
            fg=self.controller.colores['claro']['texto_suave'],
            bg=self.controller.colores['claro']['panel']
        )
        self.mensaje_carga.place(relx=0.5, rely=0.5, anchor='center')
        
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
        # Cerrar figuras anteriores para evitar fugas de memoria
        plt.close('all')
        
        # Limpiar figuras inactivas
        limpiar_figuras_inactivas()
        
        # Implementación según las necesidades
        fig, ax = plt.subplots(figsize=(ancho/100, alto/100), dpi=100)
        
        # Agregar a la lista de figuras activas con referencia débil
        global _figuras_activas
        _figuras_activas.append(weakref.ref(fig))
        
        # Guardar referencia local
        self.figuras.append(weakref.ref(fig))
        
        return fig, ax
    
    def redondear_widget(self, widget):
        """Aplica estilo redondeado a los widgets"""
        try:
            widget.config(relief=tk.FLAT, borderwidth=0)
            if hasattr(widget, 'config') and callable(getattr(widget.config, '__call__', None)):
                widget.config(highlightthickness=0)
        except Exception as e:
            logger.error(f"No se pudieron aplicar bordes redondeados: {e}")
    
    def actualizar_dashboard(self, event=None):
        """Actualiza todos los componentes del dashboard"""
        # Evitar actualizaciones si estamos en proceso de actualización
        if hasattr(self, 'actualizando_interfaz') and self.actualizando_interfaz:
            return
            
        # Verificar que todos los frames necesarios existen
        if not hasattr(self, 'kpi_frame') or not hasattr(self, 'grafico_izquierdo') or not hasattr(self, 'grafico_derecho'):
            return
            
        self.actualizando_interfaz = True
        
        try:
            # Ocultar mensaje de carga si existe
            if hasattr(self, 'mensaje_carga'):
                self.mensaje_carga.place_forget()
            
            # Filtrar datos según el periodo seleccionado
            periodo = self.periodo_var.get()
            fecha_inicio = None
            
            if periodo == "Último mes":
                fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            elif periodo == "Últimos 3 meses":
                fecha_inicio = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            elif periodo == "Último año":
                fecha_inicio = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # Filtrar datos con validación de formato de fecha
            if fecha_inicio:
                gastos_filtrados = []
                for g in self.gastos:
                    try:
                        # Asegurar que la fecha tenga el formato correcto
                        if 'fecha' in g and g['fecha'] and g['fecha'] >= fecha_inicio:
                            gastos_filtrados.append(g)
                    except (TypeError, ValueError):
                        # Ignorar datos con formato de fecha inválido
                        continue
            else:
                gastos_filtrados = self.gastos
                
            if fecha_inicio:
                ingresos_filtrados = []
                for i in self.ingresos:
                    try:
                        if 'fecha' in i and i['fecha'] and i['fecha'] >= fecha_inicio:
                            ingresos_filtrados.append(i)
                    except (TypeError, ValueError):
                        continue
            else:
                ingresos_filtrados = self.ingresos
            
            # Actualizar componentes
            self.actualizar_kpis(gastos_filtrados, ingresos_filtrados)
            self.actualizar_grafico_izquierdo(gastos_filtrados)
            self.actualizar_grafico_derecho(gastos_filtrados, ingresos_filtrados)
            self.actualizar_anomalias(gastos_filtrados)
            self.actualizar_recomendaciones(gastos_filtrados, ingresos_filtrados)
        
        except Exception as e:
            logger.error(f"Error al actualizar dashboard: {e}")
        finally:
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