# ui/presupuesto_frame.py
import logging
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('TkAgg')

from presupuesto_ia import PresupuestoInteligente
from ia_module import modulo_ia

class PresupuestoFrame(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.title("Presupuesto Inteligente")
        
        # Configurar para comportamiento nativo de ventana
        self.resizable(True, True)
        self.attributes('-alpha', 0.0)  # Ocultar temporalmente
        
        # Establecer como ventana normal, no de utilidad
        if hasattr(self, 'attributes'):
            self.attributes('-toolwindow', False)
        
        # Configurar ventana
        self.state('zoomed')
        self.configure(bg=controller.colores['claro']['panel'])
        self.minsize(1280, 920)
        
        # Vincular doble clic en la barra de título para maximizar
        self.bind('<Double-Button-1>', self._toggle_maximize)
        
        # Inicializar datos
        self.interfaz_creada = False
        self.actualizando_interfaz = False
        self.inicializar_datos()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Centrar la ventana
        self.centrar_ventana()
        
        # Hacer la ventana modal
        self.transient(parent)
        self.grab_set()
        
        # Vincular evento de redimensionamiento
        self.bind("<Configure>", self.ajustar_interfaz)
        
        # Mostrar la ventana con fade-in
        self.after(100, lambda: self.attributes('-alpha', 1.0))
        
        # Forzar actualización inicial
        self.after(200, self.actualizar_contenido)
    
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
        
        # Verificar si resumen_frame existe antes de intentar actualizar
        if hasattr(self, 'resumen_frame') and hasattr(self, 'actualizar_contenido'):
            self.actualizar_contenido()
        else:
            # Si no existe, verificar si la interfaz se ha creado
            if not self.interfaz_creada:
                self.crear_interfaz()
        
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
            
    def inicializar_datos(self):
        """Inicializa los datos necesarios para el presupuesto"""
        try:
            # Inicializar el sistema de presupuesto
            self.sistema_presupuesto = PresupuestoInteligente()
            
            # Cargar datos históricos
            from data_manager import cargar_datos
            self.gastos_recientes = cargar_datos("gastos") or []
            self.ingresos_recientes = cargar_datos("ingresos") or []
            
            # Definir métodos esperados
            self.metodos_presupuesto = {
                'obtener_presupuesto_actual': True,
                'generar_presupuesto_sugerido': True,
                'predecir_ingresos': True,
                'seguimiento_presupuesto': True
            }
            
            # Verificar existencia de métodos
            for metodo in self.metodos_presupuesto:
                self.metodos_presupuesto[metodo] = hasattr(self.sistema_presupuesto, metodo) and callable(getattr(self.sistema_presupuesto, metodo))
            
            # Obtener presupuesto actual usando un enfoque más elegante
            self.presupuesto_actual = {}
            if self.metodos_presupuesto['obtener_presupuesto_actual']:
                self.presupuesto_actual = self.sistema_presupuesto.obtener_presupuesto_actual() or {}
            
            if not self.presupuesto_actual and self.metodos_presupuesto['generar_presupuesto_sugerido']:
                self.presupuesto_actual = self.sistema_presupuesto.generar_presupuesto_sugerido() or {}
            
            # Ingresos predichos
            self.ingresos_predichos = 0
            if self.metodos_presupuesto['predecir_ingresos']:
                self.ingresos_predichos = self.sistema_presupuesto.predecir_ingresos() or 0
            elif self.ingresos_recientes:
                # Cálculo alternativo
                self.ingresos_predichos = sum(i.get('monto', 0) for i in self.ingresos_recientes) / len(self.ingresos_recientes)
            
            # Seguimiento de presupuesto
            self.seguimiento = {}
            if self.metodos_presupuesto['seguimiento_presupuesto']:
                self.seguimiento = self.sistema_presupuesto.seguimiento_presupuesto(self.gastos_recientes) or {}
                
        except Exception as e:
            print(f"Error al inicializar datos de presupuesto: {e}")
            # Valores predeterminados para evitar errores
            self.presupuesto_actual = {}
            self.gastos_recientes = []
            self.ingresos_recientes = []
            self.ingresos_predichos = 0
            self.seguimiento = {}
        
    def crear_interfaz(self):
        """Crea la interfaz del presupuesto"""
        # Evitar llamadas recursivas
        if self.interfaz_creada or self.actualizando_interfaz:
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
        
        # Título del presupuesto
        tk.Label(
            self.main_frame,
            text="Presupuesto Inteligente Mensual",
            font=("Comic Sans MS", 18, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 20))
        
        # Crear panel de controles
        controles_frame = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        controles_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Botón para regenerar presupuesto
        self.btn_regenerar = tk.Button(
            controles_frame,
            text="🔄 Regenerar Presupuesto Sugerido",
            command=self.regenerar_presupuesto,
            font=("Comic Sans MS", 11),
            bg=self.controller.colores['claro']['acento'],
            fg="white",
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.btn_regenerar.pack(side=tk.RIGHT)
        self.controller.redondear_widget(self.btn_regenerar)
        
        # Paneles principales
        paneles_frame = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        paneles_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo
        self.panel_izquierdo = tk.Frame(
            paneles_frame,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10,
            highlightbackground=self.controller.colores['claro']['borde'],
            highlightthickness=1
        )
        self.panel_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Panel derecho
        self.panel_derecho = tk.Frame(
            paneles_frame,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10,
            highlightbackground=self.controller.colores['claro']['borde'],
            highlightthickness=1
        )
        self.panel_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Crear contenido de los paneles
        self.crear_panel_izquierdo()
        self.crear_panel_derecho()
        
        # Actualizar con datos actuales
        self.actualizar_contenido()
        
        self.interfaz_creada = True
        self.actualizando_interfaz = False
    
    def crear_panel_izquierdo(self):
        """Crea el panel izquierdo con el resumen de presupuesto"""
        # Título
        tk.Label(
            self.panel_izquierdo,
            text="Resumen de Presupuesto Mensual",
            font=("Comic Sans MS", 14, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 15))
        
        # Frame para el resumen
        self.resumen_frame = tk.Frame(
            self.panel_izquierdo,
            bg=self.controller.colores['claro']['panel']
        )
        self.resumen_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame para el gráfico
        self.grafico_presupuesto_frame = tk.Frame(
            self.panel_izquierdo,
            bg=self.controller.colores['claro']['panel'],
            height=300
        )
        self.grafico_presupuesto_frame.pack(fill=tk.X, pady=(20, 0))
    
    def crear_panel_derecho(self):
        """Crea el panel derecho con el seguimiento de categorías"""
        # Título
        tk.Label(
            self.panel_derecho,
            text="Seguimiento por Categoría",
            font=("Comic Sans MS", 14, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 15))
        
        # Contenedor con scroll
        self.categorias_container = tk.Frame(
            self.panel_derecho,
            bg=self.controller.colores['claro']['panel']
        )
        self.categorias_container.pack(fill=tk.BOTH, expand=True)
    
    def redondear_widget(self, widget):
        """Aplica estilo redondeado a los widgets"""
        try:
            widget.config(relief=tk.FLAT, borderwidth=0)
            if hasattr(widget, 'config') and callable(getattr(widget.config, '__call__', None)):
                widget.config(highlightthickness=0)
        except Exception as e:
            print(f"No se pudieron aplicar bordes redondeados: {e}")
    
    def actualizar_contenido(self):
        """Actualiza todo el contenido del presupuesto"""
        # Verificar si todos los frames necesarios existen
        if not hasattr(self, 'resumen_frame') or not hasattr(self, 'grafico_presupuesto_frame') or not hasattr(self, 'categorias_container'):
            return
        
        self.actualizar_resumen()
        self.actualizar_grafico_presupuesto()
        self.actualizar_categorias()
    
    def actualizar_resumen(self):
        """Actualiza el panel de resumen"""
        # Verificar si resumen_frame existe
        if not hasattr(self, 'resumen_frame'):
            return
            
        # Limpiar frame
        for widget in self.resumen_frame.winfo_children():
            widget.destroy()
        
        # Calcular totales
        total_presupuestado = sum(cat.get('sugerido', 0) for cat in self.presupuesto_actual.values())
        total_gastado = sum(g['monto'] for g in self.gastos_recientes)
        
        # Crear frame con sombra para el resumen
        resumen_panel = tk.Frame(
            self.resumen_frame,
            bg=self.controller.colores['claro']['panel'],
            highlightbackground=self.controller.colores['claro']['borde'],
            highlightthickness=1,
            padx=15,
            pady=15
        )
        resumen_panel.pack(fill=tk.X, pady=10)
        
        # Ingresos predichos
        tk.Label(
            resumen_panel,
            text="Ingresos Mensuales Estimados:",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['texto'],
            bg=self.controller.colores['claro']['panel'],
            anchor='w'
        ).grid(row=0, column=0, sticky='w', pady=5)
        
        tk.Label(
            resumen_panel,
            text=f"${self.ingresos_predichos:.2f}",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['exito'],
            bg=self.controller.colores['claro']['panel'],
            anchor='e'
        ).grid(row=0, column=1, sticky='e', pady=5)
        
        # Presupuesto total
        tk.Label(
            resumen_panel,
            text="Presupuesto Total:",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['texto'],
            bg=self.controller.colores['claro']['panel'],
            anchor='w'
        ).grid(row=1, column=0, sticky='w', pady=5)
        
        tk.Label(
            resumen_panel,
            text=f"${total_presupuestado:.2f}",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel'],
            anchor='e'
        ).grid(row=1, column=1, sticky='e', pady=5)
        
        # Separador
        ttk.Separator(resumen_panel, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Gastos actuales
        tk.Label(
            resumen_panel,
            text="Gastos Actuales (último mes):",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['texto'],
            bg=self.controller.colores['claro']['panel'],
            anchor='w'
        ).grid(row=3, column=0, sticky='w', pady=5)
        
        tk.Label(
            resumen_panel,
            text=f"${total_gastado:.2f}",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['alerta'],
            bg=self.controller.colores['claro']['panel'],
            anchor='e'
        ).grid(row=3, column=1, sticky='e', pady=5)
        
        # Porcentaje utilizado
        porcentaje_utilizado = (total_gastado / total_presupuestado * 100) if total_presupuestado > 0 else 0
        
        tk.Label(
            resumen_panel,
            text="Porcentaje Utilizado:",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['texto'],
            bg=self.controller.colores['claro']['panel'],
            anchor='w'
        ).grid(row=4, column=0, sticky='w', pady=5)
        
        # Color según porcentaje
        color_porcentaje = self.controller.colores['claro']['exito']
        if porcentaje_utilizado > 80:
            color_porcentaje = self.controller.colores['claro']['destacado']
        if porcentaje_utilizado > 100:
            color_porcentaje = self.controller.colores['claro']['alerta']
        
        tk.Label(
            resumen_panel,
            text=f"{porcentaje_utilizado:.1f}%",
            font=("Comic Sans MS", 12, "bold"),
            fg=color_porcentaje,
            bg=self.controller.colores['claro']['panel'],
            anchor='e'
        ).grid(row=4, column=1, sticky='e', pady=5)
        
        # Restante
        restante = total_presupuestado - total_gastado
        
        tk.Label(
            resumen_panel,
            text="Restante:",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['texto'],
            bg=self.controller.colores['claro']['panel'],
            anchor='w'
        ).grid(row=5, column=0, sticky='w', pady=5)
        
        tk.Label(
            resumen_panel,
            text=f"${restante:.2f}",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['exito'] if restante >= 0 else self.controller.colores['claro']['alerta'],
            bg=self.controller.colores['claro']['panel'],
            anchor='e'
        ).grid(row=5, column=1, sticky='e', pady=5)
        
        # Configurar grid
        resumen_panel.grid_columnconfigure(0, weight=1)
        resumen_panel.grid_columnconfigure(1, weight=1)
    
    def actualizar_grafico_presupuesto(self):
        """Actualiza el gráfico de presupuesto vs gastos"""
        # Verificar si grafico_presupuesto_frame existe
        if not hasattr(self, 'grafico_presupuesto_frame'):
            return
            
        # Limpiar frame
        for widget in self.grafico_presupuesto_frame.winfo_children():
            widget.destroy()
        
        # Liberar memoria de figuras previas
        plt.close('all')
        
        # Si no hay datos, mostrar mensaje
        if not self.presupuesto_actual:
            tk.Label(
                self.grafico_presupuesto_frame,
                text="No hay datos de presupuesto disponibles",
                font=("Comic Sans MS", 12),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel']
            ).pack(pady=50)
            return
        
        # Título
        tk.Label(
            self.grafico_presupuesto_frame,
            text="Presupuesto vs Gastos",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 10))
        
        # Preparar datos para el gráfico
        categorias = []
        presupuestado = []
        gastado = []
        
        # Agrupar gastos por categoría
        gastos_por_categoria = {}
        for gasto in self.gastos_recientes:
            categoria = gasto.get('categoria', 'otros')
            if categoria not in gastos_por_categoria:
                gastos_por_categoria[categoria] = 0
            gastos_por_categoria[categoria] += gasto['monto']
        
        # Obtener solo las top 6 categorías para el gráfico
        top_categorias = sorted(
            self.presupuesto_actual.items(), 
            key=lambda x: x[1].get('sugerido', 0), 
            reverse=True
        )[:6]
        
        for categoria, datos in top_categorias:
            categorias.append(categoria)
            presupuestado.append(datos.get('sugerido', 0))
            gastado.append(gastos_por_categoria.get(categoria, 0))
        
        # Obtener dimensiones actuales
        ancho = self.grafico_presupuesto_frame.winfo_width() or 400
        alto = self.grafico_presupuesto_frame.winfo_height() or 300
        
        # Convertir a pulgadas para figsize
        ancho_fig = max(ancho - 20, 300) / 100
        alto_fig = max(alto - 20, 200) / 100
        
        # Crear figura y gráfico
        fig, ax = plt.subplots(figsize=(ancho_fig, alto_fig), dpi=100)
        
        # Configurar ancho de barras
        indice = np.arange(len(categorias))
        ancho = 0.35
        
        # Crear barras
        rects1 = ax.bar(indice - ancho/2, presupuestado, ancho, label='Presupuestado', color=self.controller.colores['claro']['acento'])
        rects2 = ax.bar(indice + ancho/2, gastado, ancho, label='Gastado', color=self.controller.colores['claro']['alerta'])
        
        # Personalizar gráfico
        ax.set_ylabel('Monto ($)')
        ax.set_title('Comparativa por Categoría')
        ax.set_xticks(indice)
        ax.set_xticklabels(categorias, rotation=45, ha='right')
        ax.legend()
        
        plt.tight_layout()
        
        # Crear un frame contenedor para el gráfico que se ajuste
        canvas_frame = tk.Frame(self.grafico_presupuesto_frame, bg=self.controller.colores['claro']['panel'])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Incrustar gráfico en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def actualizar_categorias(self):
        """Actualiza el panel de seguimiento por categoría"""
        # Verificar si categorias_container existe
        if not hasattr(self, 'categorias_container'):
            return
            
        # Limpiar frame
        for widget in self.categorias_container.winfo_children():
            widget.destroy()
        
        # Si no hay datos, mostrar mensaje
        if not self.seguimiento:
            tk.Label(
                self.categorias_container,
                text="No hay datos de seguimiento disponibles",
                font=("Comic Sans MS", 12),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel']
            ).pack(pady=50)
            return
        
        # Crear contenedor con scroll
        canvas = tk.Canvas(
            self.categorias_container,
            bg=self.controller.colores['claro']['panel'],
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(self.categorias_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.controller.colores['claro']['panel'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Ordenar categorías por porcentaje utilizado (mayor primero)
        categorias_ordenadas = sorted(
            self.seguimiento.items(), 
            key=lambda x: x[1]['porcentaje_utilizado'], 
            reverse=True
        )
        
        # Mostrar cada categoría
        for categoria, datos in categorias_ordenadas:
            # Crear frame para la categoría
            cat_frame = tk.Frame(
                scrollable_frame,
                bg=self.controller.colores['claro']['panel'],
                highlightbackground=self.controller.colores['claro']['borde'],
                highlightthickness=1,
                padx=15,
                pady=15,
                bd=0
            )
            cat_frame.pack(fill=tk.X, pady=10)
            
            # Título y estado
            estado = datos['estado']
            color_estado = {
                'bueno': self.controller.colores['claro']['exito'],
                'alerta': self.controller.colores['claro']['destacado'],
                'excedido': self.controller.colores['claro']['alerta']
            }.get(estado, self.controller.colores['claro']['texto'])
            
            icono_estado = {
                'bueno': '✅',
                'alerta': '⚠️',
                'excedido': '❌'
            }.get(estado, '⚪')
            
            # Header frame
            header_frame = tk.Frame(cat_frame, bg=self.controller.colores['claro']['panel'])
            header_frame.pack(fill=tk.X)
            
            # Título
            tk.Label(
                header_frame,
                text=categoria.capitalize(),
                font=("Comic Sans MS", 12, "bold"),
                fg=self.controller.colores['claro']['texto'],
                bg=self.controller.colores['claro']['panel'],
                anchor='w'
            ).pack(side=tk.LEFT)
            
            # Estado
            tk.Label(
                header_frame,
                text=f"{icono_estado} {datos['porcentaje_utilizado']:.1f}%",
                font=("Comic Sans MS", 12, "bold"),
                fg=color_estado,
                bg=self.controller.colores['claro']['panel'],
                anchor='e'
            ).pack(side=tk.RIGHT)
            
            # Crear barra de progreso
            barra_frame = tk.Frame(cat_frame, bg=self.controller.colores['claro']['panel'], pady=10)
            barra_frame.pack(fill=tk.X)
            
            # Canvas para la barra
            barra_height = 15
            barra_canvas = tk.Canvas(
                barra_frame,
                width=400,
                height=barra_height,
                bg=self.controller.colores['claro']['borde'],
                highlightthickness=0
            )
            barra_canvas.pack(fill=tk.X)
            
            # Calcular ancho de la barra de progreso
            porcentaje = min(datos['porcentaje_utilizado'], 100)  # Limitar al 100% para la visualización
            ancho_barra = (porcentaje / 100) * 400
            # Color de la barra según estado
            color_barra = color_estado
            
            # Dibujar barra
            barra_canvas.create_rectangle(
                0, 0, ancho_barra, barra_height,
                fill=color_barra,
                outline=""
            )
            
            # Si excede el 100%, mostrar línea roja
            if datos['porcentaje_utilizado'] > 100:
                # Dibujar línea del 100%
                barra_canvas.create_line(
                    400, 0, 400, barra_height,
                    fill=self.controller.colores['claro']['alerta'],
                    width=2
                )
            
            # Información detallada
            info_frame = tk.Frame(cat_frame, bg=self.controller.colores['claro']['panel'], pady=5)
            info_frame.pack(fill=tk.X)
            
            # Presupuesto vs Gastado
            tk.Label(
                info_frame,
                text=f"Presupuesto: ${datos['presupuesto']:.2f}",
                font=("Comic Sans MS", 10),
                fg=self.controller.colores['claro']['texto'],
                bg=self.controller.colores['claro']['panel'],
                anchor='w'
            ).grid(row=0, column=0, sticky='w')
            
            tk.Label(
                info_frame,
                text=f"Gastado: ${datos['gasto_actual']:.2f}",
                font=("Comic Sans MS", 10),
                fg=self.controller.colores['claro']['texto'],
                bg=self.controller.colores['claro']['panel'],
                anchor='e'
            ).grid(row=0, column=1, sticky='e')
            
            # Restante
            tk.Label(
                info_frame,
                text=f"Restante: ${datos['restante']:.2f}",
                font=("Comic Sans MS", 10, "bold"),
                fg=self.controller.colores['claro']['exito'] if datos['restante'] >= 0 else self.controller.colores['claro']['alerta'],
                bg=self.controller.colores['claro']['panel'],
                anchor='w'
            ).grid(row=1, column=0, sticky='w', pady=(5, 0))
            
            # Configurar grid
            info_frame.grid_columnconfigure(0, weight=1)
            info_frame.grid_columnconfigure(1, weight=1)
    
    def regenerar_presupuesto(self):
        """Regenera el presupuesto sugerido basado en el análisis de IA"""
        # Confirmación
        respuesta = messagebox.askyesno(
            "Regenerar Presupuesto",
            "¿Está seguro que desea regenerar el presupuesto? Esto reemplazará su presupuesto actual."
        )
        
        if respuesta:
            try:
                # Regenerar presupuesto
                self.presupuesto_actual = self.sistema_presupuesto.generar_presupuesto_sugerido()
                
                # Recalcular seguimiento
                self.seguimiento = self.sistema_presupuesto.seguimiento_presupuesto(self.gastos_recientes)
                
                # Actualizar interfaz
                self.actualizar_contenido()
                
                messagebox.showinfo(
                    "Presupuesto Regenerado",
                    "El presupuesto ha sido regenerado exitosamente basado en sus patrones históricos de gastos e ingresos."
                )
            except Exception as e:
                print(f"Error al regenerar presupuesto: {e}")
                messagebox.showerror(
                    "Error",
                    f"No se pudo regenerar el presupuesto: {e}"
                )