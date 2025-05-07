# ui/dolar_widget_realtime.py
import sys
import tkinter as tk
from tkinter import ttk
import requests
import json
import time
from datetime import datetime
import threading

# URLs de las APIs como constantes
API_BLUELYTICS = 'https://api.bluelytics.com.ar/v2/latest'
API_DOLARAPI = 'https://dolarapi.com/v1/dolares'

class DolarWidgetRealtime(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.title("Cotización del Dólar")
        
        # Configurar para comportamiento nativo de ventana
        self.resizable(True, True)
        self.attributes('-alpha', 0.0)  # Ocultar temporalmente
        
        # Establecer como ventana normal, no de utilidad
        if hasattr(self, 'attributes'):
            self.attributes('-toolwindow', False)
        
        # Configurar la ventana
        self.geometry("380x400")  # Aumentar el tamaño para evitar que se corte
        self.configure(bg=controller.colores['claro']['panel'])
        self.minsize(380, 400)
        
        # Vincular doble clic en la barra de título para maximizar
        self.bind('<Double-Button-1>', self._toggle_maximize)
        
        # Inicializar datos
        self.interfaz_creada = False
        self.actualizando_interfaz = False
        self.ultimo_intento = 0
        self.datos_dolar = {
            "oficial": {"compra": "---", "venta": "---"},
            "blue": {"compra": "---", "venta": "---"},
            "bolsa": {"compra": "---", "venta": "---"},
            "turista": {"compra": "---", "venta": "---"},
            "ccl": {"compra": "---", "venta": "---"}
        }
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Centrar la ventana
        self.centrar_ventana()
        
        # No hacer la ventana modal para permitir usar la app mientras está abierta
        self.transient(parent)
        
        # Vincular evento de redimensionamiento
        self.bind("<Configure>", self.ajustar_interfaz)
        
        # Mostrar la ventana con fade-in
        self.after(100, lambda: self.attributes('-alpha', 1.0))
        
        # Forzar actualización inicial
        self.after(200, self.obtener_datos_dolar)
    
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
        
        # Verificar si tipos_frame existe antes de intentar actualizar
        if hasattr(self, 'tipos_frame'):
            # Actualizar la tabla de cotizaciones para ajustarla al nuevo tamaño
            self.crear_tabla_cotizaciones()
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
    
    def crear_interfaz(self):
        """Crea la interfaz del widget de dólar"""
        # Evitar llamadas recursivas
        if hasattr(self, 'interfaz_creada') and self.interfaz_creada:
            return
            
        self.actualizando_interfaz = True
        
        # Frame principal con padding
        self.main_frame = tk.Frame(
            self, 
            bg=self.controller.colores['claro']['panel'],
            padx=15, 
            pady=15
        )
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo_frame = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        titulo_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            titulo_frame,
            text="💰 Cotización del Dólar",
            font=("Comic Sans MS", 16, "bold"),
            fg=self.controller.colores['claro']['acento'],
            bg=self.controller.colores['claro']['panel']
        ).pack(anchor='center')
        
        # Fecha actual
        self.lbl_fecha = tk.Label(
            titulo_frame,
            text=self.obtener_fecha_formateada(),
            font=("Comic Sans MS", 10),
            fg=self.controller.colores['claro']['texto'],
            bg=self.controller.colores['claro']['panel']
        )
        self.lbl_fecha.pack(anchor='center', pady=(5, 0))
        
        # Separador
        ttk.Separator(self.main_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Contenedor para los tipos de dólar
        self.tipos_frame = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        self.tipos_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Crear tabla de cotizaciones
        self.crear_tabla_cotizaciones()
        
        # Panel de botones
        botones_frame = tk.Frame(self.main_frame, bg=self.controller.colores['claro']['panel'])
        botones_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Botón de actualizar
        self.btn_actualizar = tk.Button(
            botones_frame,
            text="🔄 Actualizar ahora",
            command=self.forzar_actualizacion,
            font=("Comic Sans MS", 10),
            bg=self.controller.colores['claro']['acento'],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.btn_actualizar.pack(side=tk.LEFT)
        
        # Etiqueta para mostrar la última actualización
        self.lbl_actualizacion = tk.Label(
            self.main_frame,
            text="Actualizando...",
            font=("Comic Sans MS", 8),
            fg=self.controller.colores['claro']['texto_suave'],
            bg=self.controller.colores['claro']['panel']
        )
        self.lbl_actualizacion.pack(pady=(10, 0), anchor='e')
        
        self.interfaz_creada = True
        self.actualizando_interfaz = False
    
    def crear_tabla_cotizaciones(self):
        """Crea una tabla para mostrar las cotizaciones"""
        # Verificar si tipos_frame existe
        if not hasattr(self, 'tipos_frame'):
            return
            
        # Limpiar el frame si ya tiene widgets
        for widget in self.tipos_frame.winfo_children():
            widget.destroy()
        
        # Crear cabeceras
        cabeceras = ["Tipo", "Compra", "Venta"]
        for i, texto in enumerate(cabeceras):
            lbl = tk.Label(
                self.tipos_frame,
                text=texto,
                font=("Comic Sans MS", 11, "bold"),
                fg=self.controller.colores['claro']['texto'],
                bg=self.controller.colores['claro']['borde'],
                padx=5, 
                pady=5
            )
            lbl.grid(row=0, column=i, sticky='ew', padx=1, pady=1)
        
        # Configurar ancho de columnas
        self.tipos_frame.grid_columnconfigure(0, weight=2)
        self.tipos_frame.grid_columnconfigure(1, weight=1)
        self.tipos_frame.grid_columnconfigure(2, weight=1)
        
        # Crear filas para cada tipo de dólar
        tipos_nombres = {
            "oficial": "Oficial",
            "blue": "Blue",
            "ccl": "CCL",
            "bolsa": "MEP",
            "turista": "Turista"
        }
        
        # Crear la tabla
        self.labels_valores = {}
        fila = 1
        for tipo_id, tipo_nombre in tipos_nombres.items():
            color_fila = self.controller.colores['claro']['panel'] if fila % 2 == 0 else self.controller.colores['claro']['fondo']
            
            # Tipo de dólar
            tk.Label(
                self.tipos_frame,
                text=tipo_nombre,
                font=("Comic Sans MS", 10, "bold"),
                fg=self.controller.colores['claro']['texto'],
                bg=color_fila,
                anchor='w',
                padx=5, 
                pady=5
            ).grid(row=fila, column=0, sticky='ew', padx=1, pady=1)
            
            # Compra
            self.labels_valores[f"{tipo_id}_compra"] = tk.Label(
                self.tipos_frame,
                text="$ " + self.datos_dolar[tipo_id]["compra"],
                font=("Comic Sans MS", 10),
                fg=self.controller.colores['claro']['texto'],
                bg=color_fila,
                anchor='e',
                padx=5
            )
            self.labels_valores[f"{tipo_id}_compra"].grid(row=fila, column=1, sticky='ew', padx=1, pady=1)
            
            # Venta
            self.labels_valores[f"{tipo_id}_venta"] = tk.Label(
                self.tipos_frame,
                text="$ " + self.datos_dolar[tipo_id]["venta"],
                font=("Comic Sans MS", 10),
                fg=self.controller.colores['claro']['texto'],
                bg=color_fila,
                anchor='e',
                padx=5
            )
            self.labels_valores[f"{tipo_id}_venta"].grid(row=fila, column=2, sticky='ew', padx=1, pady=1)
            
            fila += 1
    
    def obtener_fecha_formateada(self):
        """Obtiene la fecha actual formateada"""
        fecha_actual = datetime.now()
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        
        dia_semana = dias[fecha_actual.weekday()]
        dia = fecha_actual.day
        mes = meses[fecha_actual.month - 1]
        año = fecha_actual.year
        
        return f"{dia_semana} {dia} de {mes} de {año}"
    
    def obtener_datos_dolar(self):
        """Obtiene los datos actualizados del dólar"""
        # Verificar si hay demasiadas solicitudes recientes
        tiempo_actual = time.time()
        if tiempo_actual - self.ultimo_intento < 5:  # Evitar peticiones muy seguidas
            return
        
        self.ultimo_intento = tiempo_actual
        
        # Usar threading para evitar bloquear la interfaz
        threading.Thread(target=self._obtener_datos_en_hilo, daemon=True).start()
    
    def _obtener_datos_en_hilo(self):
        """Obtiene datos en un hilo separado"""
        try:
            # Obtener datos de la primera API
            datos_obtenidos = False
            try:
                response = requests.get(API_BLUELYTICS, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # Actualizar datos
                    self.datos_dolar["oficial"]["compra"] = str(data["oficial"]["value_buy"])
                    self.datos_dolar["oficial"]["venta"] = str(data["oficial"]["value_sell"])
                    self.datos_dolar["blue"]["compra"] = str(data["blue"]["value_buy"])
                    self.datos_dolar["blue"]["venta"] = str(data["blue"]["value_sell"])
                    
                    # Calcular valores aproximados para los otros tipos
                    valor_oficial = float(data["oficial"]["value_sell"])
                    
                    # Estos son aproximados basados en patrones típicos
                    self.datos_dolar["bolsa"]["compra"] = str(round(valor_oficial * 0.98, 2))
                    self.datos_dolar["bolsa"]["venta"] = str(round(valor_oficial * 1.03, 2))
                    self.datos_dolar["ccl"]["compra"] = str(round(valor_oficial * 0.99, 2))
                    self.datos_dolar["ccl"]["venta"] = str(round(valor_oficial * 1.04, 2))
                    self.datos_dolar["turista"]["compra"] = "---"
                    self.datos_dolar["turista"]["venta"] = str(round(valor_oficial * 1.30, 2))
                    datos_obtenidos = True
            except requests.exceptions.RequestException as e:
                print(f"Error al conectar con API primaria: {e}")
            
            # Intentar con API alternativa para complementar o sustituir datos
            try:
                alt_response = requests.get(API_DOLARAPI, timeout=5)
                if alt_response.status_code == 200:
                    alt_data = alt_response.json()
                    for item in alt_data:
                        if item.get("casa") == "oficial":
                            self.datos_dolar["oficial"]["compra"] = str(item.get("compra", self.datos_dolar["oficial"]["compra"]))
                            self.datos_dolar["oficial"]["venta"] = str(item.get("venta", self.datos_dolar["oficial"]["venta"]))
                        elif item.get("casa") == "blue":
                            self.datos_dolar["blue"]["compra"] = str(item.get("compra", self.datos_dolar["blue"]["compra"]))
                            self.datos_dolar["blue"]["venta"] = str(item.get("venta", self.datos_dolar["blue"]["venta"]))
                        elif item.get("casa") in ["bolsa", "mep"]:
                            self.datos_dolar["bolsa"]["compra"] = str(item.get("compra", self.datos_dolar["bolsa"]["compra"]))
                            self.datos_dolar["bolsa"]["venta"] = str(item.get("venta", self.datos_dolar["bolsa"]["venta"]))
                        elif item.get("casa") in ["contadoconliqui", "ccl"]:
                            self.datos_dolar["ccl"]["compra"] = str(item.get("compra", self.datos_dolar["ccl"]["compra"]))
                            self.datos_dolar["ccl"]["venta"] = str(item.get("venta", self.datos_dolar["ccl"]["venta"]))
                        elif item.get("casa") in ["turista", "tarjeta"]:
                            self.datos_dolar["turista"]["compra"] = str(item.get("compra", self.datos_dolar["turista"]["compra"]))
                            self.datos_dolar["turista"]["venta"] = str(item.get("venta", self.datos_dolar["turista"]["venta"]))
                    datos_obtenidos = True
            except requests.exceptions.RequestException as e:
                print(f"Error al conectar con API alternativa: {e}")
                
            # Actualizar la interfaz solo si obtuvimos datos
            if datos_obtenidos:
                # Usar after para actualizar en el hilo principal
                self.after(0, self.actualizar_interfaz_dolar)
            else:
                self.after(0, lambda: self.lbl_actualizacion.config(text="Error al actualizar. Reintentando...") if hasattr(self, 'lbl_actualizacion') else None)
        
        except Exception as e:
            print(f"Error al procesar datos del dólar: {e}")
            # Actualizar label de error en hilo principal
            self.after(0, lambda: self.lbl_actualizacion.config(text="Error al actualizar. Reintentando...") if hasattr(self, 'lbl_actualizacion') else None)
    
    def actualizar_interfaz_dolar(self):
        """Actualiza todos los elementos de la interfaz con los datos más recientes"""
        # Actualizar los valores en la tabla
        if hasattr(self, 'labels_valores'):
            for tipo in self.datos_dolar:
                if f"{tipo}_compra" in self.labels_valores:
                    self.labels_valores[f"{tipo}_compra"].config(text="$ " + self.datos_dolar[tipo]["compra"])
                    self.labels_valores[f"{tipo}_venta"].config(text="$ " + self.datos_dolar[tipo]["venta"])
        
        # Actualizar la etiqueta de fecha
        if hasattr(self, 'lbl_fecha'):
            self.lbl_fecha.config(text=self.obtener_fecha_formateada())
        
        # Actualizar la etiqueta de última actualización
        if hasattr(self, 'lbl_actualizacion'):
            fecha_hora_actual = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
            self.lbl_actualizacion.config(text=f"Actualizado: {fecha_hora_actual}")
    
    def forzar_actualizacion(self):
        """Fuerza una actualización inmediata de los datos"""
        # Cambiar texto del botón temporalmente
        if hasattr(self, 'btn_actualizar'):
            self.btn_actualizar.config(text="Actualizando...", state=tk.DISABLED)
        
        # Reiniciar el timer para permitir actualización inmediata
        self.ultimo_intento = 0
        
        # Iniciar hilo para no bloquear la interfaz
        threading.Thread(target=self.actualizar_con_delay, daemon=True).start()
    
    def actualizar_con_delay(self):
        """Actualiza los datos y restaura el botón"""
        # Obtener datos
        self.obtener_datos_dolar()
        
        # Restaurar el botón después de un breve delay
        self.after(1000, self.restaurar_boton)
    
    def restaurar_boton(self):
        """Restaura el estado del botón de actualización"""
        if hasattr(self, 'btn_actualizar'):
            self.btn_actualizar.config(text="🔄 Actualizar ahora", state=tk.NORMAL)
    
    def actualizar_timer(self):
        """Configura un temporizador para actualizar periódicamente los datos"""
        # Iniciar un hilo para obtener los datos sin bloquear la interfaz
        threading.Thread(target=self.obtener_datos_dolar, daemon=True).start()
        
        # Programar próxima actualización en 10 segundos
        self.after(10000, self.actualizar_timer)

class DolarFloatingWidgetRealtime:
    """Widget flotante para mostrar la cotización del dólar con datos en tiempo real"""
    def __init__(self, controller):
        self.controller = controller
        self.dolar_window = None
    
    def mostrar_widget(self):
        """Muestra la ventana del widget de dólar"""
        # Si ya está abierta, traerla al frente
        if self.dolar_window and self.dolar_window.winfo_exists():
            self.dolar_window.lift()
            self.dolar_window.focus_force()
            return
        
        # Crear nueva ventana
        self.dolar_window = DolarWidgetRealtime(self.controller.root, self.controller)