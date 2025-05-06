# ui/categoria_analisis.py
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('TkAgg')

from model.ia_module import modulo_ia
from model.data_manager import cargar_datos

class CategoriaAnalisis(tk.Toplevel):
    def __init__(self, parent, controller, categoria):
        super().__init__(parent)
        self.controller = controller
        self.categoria = categoria
        self.title(f"Análisis Detallado: {categoria.capitalize()}")
        self.geometry("800x600")
        self.configure(bg=controller.colores['claro']['panel'])
        
        # Permitir redimensionar la ventana
        self.resizable(True, True)
        
        # Permitir maximizar/minimizar
        self.minsize(600, 450)  # Tamaño mínimo
        
        # Agregar botón de maximizar en la parte superior
        self.agregar_botones_ventana()
        
        # Hacer la ventana modal
        self.transient(parent)
        self.grab_set()
        
        # Centrar la ventana
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry('{}x{}+{}+{}'.format(ancho, alto, x, y))
        
        # Cargar y procesar datos
        self.cargar_datos()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Vincular evento de redimensionamiento
        self.bind("<Configure>", self.ajustar_graficos)
        
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
    
    def ajustar_graficos(self, event=None):
        """Ajusta los gráficos cuando cambia el tamaño de la ventana"""
        # Solo responder a cambios de tamaño de la ventana principal
        if event and event.widget != self:
            return
            
        # Dar tiempo para que la ventana se actualice
        self.after(200, self.recrear_graficos)
    
    def recrear_graficos(self):
        """Recrea los gráficos con el nuevo tamaño de ventana"""
        if hasattr(self, 'graficos_frame'):
            # Limpiar los frames de gráficos existentes
            for widget in self.graficos_frame.winfo_children():
                widget.destroy()
            
            # Volver a crear los gráficos
            self.crear_graficos()
    
    def cargar_datos(self):
        """Carga y procesa los datos para el análisis de la categoría"""
        try:
            # Cargar datos crudos
            gastos_raw = cargar_datos('gastos')
            
            # Procesar datos con el módulo de IA
            gastos_procesados = modulo_ia.procesar_gastos(gastos_raw)
            
            # Filtrar por categoría
            self.gastos_categoria = [g for g in gastos_procesados if g['categoria'] == self.categoria]
            
            print(f"Datos cargados para categoría {self.categoria}: {len(self.gastos_categoria)} gastos")
        except Exception as e:
            print(f"Error al cargar datos para análisis de categoría: {e}")
            self.gastos_categoria = []
    
    def crear_interfaz(self):
        """Crea la interfaz del análisis de categoría"""
        # Frame principal con borde y padding
        self.main_frame = tk.Frame(
            self, 
            bg=self.controller.colores['claro']['panel'],
            padx=20, 
            pady=20
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo_frame = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        titulo_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            titulo_frame,
            text=f"Análisis de Categoría: {self.categoria.capitalize()}",
            font=("Comic Sans MS", 18, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(side=tk.LEFT)
        
        # Crear contenedores para gráficos y estadísticas
        self.crear_contenedores()
        
        # Botón para cerrar
        btn_cerrar = tk.Button(
            self.main_frame,
            text="Cerrar",
            command=self.destroy,
            font=("Comic Sans MS", 12),
            bg=self.controller.colores['claro']['acento'],
            fg="white",
            padx=20,
            pady=5,
            relief=tk.FLAT,
            cursor="hand2"
        )
        btn_cerrar.pack(pady=(20, 0))
        self.redondear_widget(btn_cerrar)
    
    def crear_contenedores(self):
        """Crea los contenedores para los diferentes elementos del análisis"""
        # Si no hay datos, mostrar mensaje
        if not self.gastos_categoria:
            tk.Label(
                self.main_frame,
                text=f"No hay datos disponibles para la categoría '{self.categoria}'",
                font=("Comic Sans MS", 14),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel']
            ).pack(pady=50)
            return
        
        # Panel superior: estadísticas clave
        self.estadisticas_frame = tk.Frame(
            self.main_frame,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10
        )
        self.estadisticas_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Mostrar estadísticas
        self.mostrar_estadisticas()
        
        # Panel gráficos: 2 gráficos en fila
        self.graficos_frame = tk.Frame(
            self.main_frame,
            bg=self.controller.colores['claro']['panel']
        )
        self.graficos_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear gráficos
        self.crear_graficos()
        
        # Panel recomendaciones
        self.recomendaciones_frame = tk.Frame(
            self.main_frame,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10
        )
        self.recomendaciones_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Mostrar recomendaciones
        self.mostrar_recomendaciones()
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas clave de la categoría"""
        # Calcular estadísticas
        montos = [g['monto'] for g in self.gastos_categoria]
        total = sum(montos)
        promedio = total / len(montos) if montos else 0
        minimo = min(montos) if montos else 0
        maximo = max(montos) if montos else 0
        
        # Crear tarjetas de estadísticas
        stats = [
            {"nombre": "Total", "valor": f"${total:.2f}", "color": self.controller.colores['claro']['acento']},
            {"nombre": "Promedio", "valor": f"${promedio:.2f}", "color": self.controller.colores['claro']['texto']},
            {"nombre": "Mínimo", "valor": f"${minimo:.2f}", "color": self.controller.colores['claro']['exito']},
            {"nombre": "Máximo", "valor": f"${maximo:.2f}", "color": self.controller.colores['claro']['alerta']},
            {"nombre": "Cantidad", "valor": f"{len(montos)}", "color": self.controller.colores['claro']['destacado']}
        ]
        
        # Mostrar tarjetas
        for i, stat in enumerate(stats):
            card = tk.Frame(
                self.estadisticas_frame,
                bg=self.controller.colores['claro']['panel'],
                highlightbackground=stat["color"],
                highlightthickness=2,
                padx=15,
                pady=10
            )
            card.grid(row=0, column=i, padx=5, sticky='nsew')
            
            # Configurar grid
            self.estadisticas_frame.grid_columnconfigure(i, weight=1)
            
            # Valor 
            tk.Label(
                card,
                text=stat["valor"],
                font=("Comic Sans MS", 16, "bold"),
                fg=stat["color"],
                bg=self.controller.colores['claro']['panel']
            ).pack()
            
            # Nombre
            tk.Label(
                card,
                text=stat["nombre"],
                font=("Comic Sans MS", 12),
                fg=self.controller.colores['claro']['texto'],
                bg=self.controller.colores['claro']['panel']
            ).pack()
    
    def crear_graficos(self):
        """Crea los gráficos para el análisis"""
        # Frame izquierdo: tendencia mensual
        grafico_izq = tk.Frame(
            self.graficos_frame,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10,
            width=380,
            height=300
        )
        grafico_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        grafico_izq.pack_propagate(False)
        
        # Frame derecho: distribución por monto
        grafico_der = tk.Frame(
            self.graficos_frame,
            bg=self.controller.colores['claro']['panel'],
            padx=10,
            pady=10,
            width=380,
            height=300
        )
        grafico_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        grafico_der.pack_propagate(False)
        
        # Crear gráfico de tendencia
        self.crear_grafico_tendencia(grafico_izq)
        
        # Crear gráfico de distribución
        self.crear_grafico_distribucion(grafico_der)
    
    def crear_grafico_tendencia(self, frame):
        """Crea un gráfico de tendencia mensual"""
        # Título
        tk.Label(
            frame,
            text="Tendencia Mensual",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 10))
        
        # Agrupar por mes
        gastos_por_mes = {}
        
        for gasto in self.gastos_categoria:
            try:
                fecha = datetime.strptime(gasto['fecha'], "%Y-%m-%d")
                clave_mes = f"{fecha.year}-{fecha.month:02d}"
                
                if clave_mes not in gastos_por_mes:
                    gastos_por_mes[clave_mes] = 0
                
                gastos_por_mes[clave_mes] += gasto['monto']
            except:
                continue
        
        # Si no hay datos, mostrar mensaje
        if not gastos_por_mes:
            tk.Label(
                frame,
                text="No hay suficientes datos para mostrar tendencias",
                font=("Comic Sans MS", 11),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel']
            ).pack(pady=30)
            return
        
        # Ordenar por fecha
        meses_ordenados = sorted(gastos_por_mes.keys())
        valores = [gastos_por_mes[mes] for mes in meses_ordenados]
        
        # Crear etiquetas legibles
        etiquetas = []
        for mes in meses_ordenados:
            try:
                fecha = datetime.strptime(mes, "%Y-%m")
                etiqueta = fecha.strftime("%b %y")
                etiquetas.append(etiqueta)
            except:
                etiquetas.append(mes)
        
        # Crear figura y gráfico
        fig, ax = plt.subplots(figsize=(4, 3.5), dpi=100)
        
        # Crear línea de tendencia
        ax.plot(etiquetas, valores, 'o-', color=self.controller.colores['claro']['acento'], linewidth=2, markersize=6)
        
        # Añadir línea de tendencia promedio
        promedio = sum(valores) / len(valores)
        ax.axhline(y=promedio, color=self.controller.colores['claro']['texto_suave'], linestyle='--', alpha=0.7)
        
        # Personalizar gráfico
        ax.set_xlabel('Mes')
        ax.set_ylabel('Gasto Total ($)')
        ax.grid(True, alpha=0.3)
        
        # Rotar etiquetas para mejor lectura
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Incrustar gráfico en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def crear_grafico_distribucion(self, frame):
        """Crea un gráfico de distribución de gastos"""
        # Título
        tk.Label(
            frame,
            text="Distribución de Montos",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 10))
        
        # Obtener montos
        montos = [g['monto'] for g in self.gastos_categoria]
        
        # Si no hay suficientes datos, mostrar mensaje
        if len(montos) < 3:
            tk.Label(
                frame,
                text="No hay suficientes datos para mostrar distribución",
                font=("Comic Sans MS", 11),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel']
            ).pack(pady=30)
            return
        
        # Crear figura y gráfico
        fig, ax = plt.subplots(figsize=(4, 3.5), dpi=100)
        
        # Crear histograma
        n, bins, patches = ax.hist(montos, bins=10, color=self.controller.colores['claro']['acento_oscuro'], alpha=0.7)
        
        # Personalizar gráfico
        ax.set_xlabel('Monto ($)')
        ax.set_ylabel('Frecuencia')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Incrustar gráfico en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def mostrar_recomendaciones(self):
        """Muestra recomendaciones específicas para la categoría"""
        # Título
        tk.Label(
            self.recomendaciones_frame,
            text="Recomendaciones para Optimizar",
            font=("Comic Sans MS", 12, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='w', pady=(0, 10))
        
        # Generar recomendaciones específicas según la categoría
        recomendaciones = self.generar_recomendaciones_categoria()
        
        # Crear panel para las recomendaciones
        panel = tk.Frame(
            self.recomendaciones_frame,
            bg=self.controller.colores['claro']['panel'],
            highlightbackground=self.controller.colores['claro']['borde'],
            highlightthickness=1,
            padx=15,
            pady=15
        )
        panel.pack(fill=tk.X)
        
        # Mostrar recomendaciones
        for i, rec in enumerate(recomendaciones):
            # Icono
            if i > 0:
                ttk.Separator(panel, orient='horizontal').pack(fill=tk.X, pady=10)
                
            rec_frame = tk.Frame(panel, bg=self.controller.colores['claro']['panel'])
            rec_frame.pack(fill=tk.X)
            
            tk.Label(
                rec_frame,
                text=rec["icono"],
                font=("Comic Sans MS", 14),
                fg=self.controller.colores['claro']['acento'],
                bg=self.controller.colores['claro']['panel']
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            # Texto principal
            texto_frame = tk.Frame(rec_frame, bg=self.controller.colores['claro']['panel'])
            texto_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            tk.Label(
                texto_frame,
                text=rec["titulo"],
                font=("Comic Sans MS", 11, "bold"),
                fg=self.controller.colores['claro']['texto'],
                bg=self.controller.colores['claro']['panel'],
                anchor='w',
                justify='left'
            ).pack(fill=tk.X)
            
            tk.Label(
                texto_frame,
                text=rec["detalle"],
                font=("Comic Sans MS", 10),
                fg=self.controller.colores['claro']['texto_suave'],
                bg=self.controller.colores['claro']['panel'],
                wraplength=650,
                anchor='w',
                justify='left'
            ).pack(fill=tk.X)
    
    def generar_recomendaciones_categoria(self):
        """Genera recomendaciones específicas para la categoría"""
        # Análisis básico
        montos = [g['monto'] for g in self.gastos_categoria]
        total = sum(montos)
        promedio = total / len(montos) if montos else 0
        maximo = max(montos) if montos else 0
        
        # Recomendaciones por defecto
        recomendaciones = [
            {
                "icono": "💡",
                "titulo": "Establezca un presupuesto mensual",
                "detalle": f"Basado en su historial, un presupuesto razonable para {self.categoria} sería de ${promedio:.2f} por mes."
            }
        ]
        
        # Recomendaciones específicas por categoría
        if self.categoria == 'alimentación':
            recomendaciones.append({
                "icono": "🛒",
                "titulo": "Planifique sus compras semanalmente",
                "detalle": "Hacer una lista de compras y planificar comidas puede reducir en promedio un 20% el gasto en alimentación."
            })
            recomendaciones.append({
                "icono": "🏪",
                "titulo": "Compare precios entre supermercados",
                "detalle": "Utilizar aplicaciones de comparación de precios o visitar diferentes supermercados puede generar ahorros significativos."
            })
            
        elif self.categoria == 'transporte':
            recomendaciones.append({
                "icono": "🚗",
                "titulo": "Considere opciones de transporte compartido",
                "detalle": "El carpooling o compartir viajes puede reducir sus gastos de combustible hasta en un 50%."
            })
            recomendaciones.append({
                "icono": "⛽",
                "titulo": "Monitoree los precios de combustible",
                "detalle": "Utilice aplicaciones para encontrar las estaciones con mejor precio y cargue combustible en días con tarifas más bajas."
            })
            
        elif self.categoria == 'servicios':
            recomendaciones.append({
                "icono": "💼",
                "titulo": "Revise sus planes y suscripciones",
                "detalle": "Verifique si puede obtener mejores tarifas o si está pagando por servicios que no utiliza frecuentemente."
            })
            recomendaciones.append({
                "icono": "💡",
                "titulo": "Optimice el consumo energético",
                "detalle": "Pequeños cambios en los hábitos de consumo pueden reducir significativamente las facturas de servicios."
            })
            
        elif self.categoria == 'ocio':
            recomendaciones.append({
                "icono": "🎭",
                "titulo": "Busque alternativas gratuitas o de bajo costo",
                "detalle": "Explore eventos comunitarios, promociones y días con descuentos especiales."
            })
            recomendaciones.append({
                "icono": "💸",
                "titulo": "Establezca un límite mensual",
                "detalle": f"Basado en su gasto promedio (${promedio:.2f}), considere establecer un límite fijo mensual para actividades de ocio."
            })
            
        # Añadir recomendación genérica sobre gastos excesivos si aplica
        if maximo > promedio * 2:
            recomendaciones.append({
                "icono": "⚠️",
                "titulo": "Atención a gastos puntuales elevados",
                "detalle": f"Se detectaron gastos muy por encima del promedio (máx: ${maximo:.2f}). Considere si estos gastos excepcionales pueden evitarse en el futuro."
            })
        
        return recomendaciones
    
    def redondear_widget(self, widget):
        """Aplica estilo redondeado a los widgets"""
        try:
            widget.config(relief=tk.FLAT, borderwidth=0)
            if hasattr(widget, 'config') and callable(getattr(widget.config, '__call__', None)):
                widget.config(highlightthickness=0)
        except Exception as e:
            print(f"No se pudieron aplicar bordes redondeados: {e}")