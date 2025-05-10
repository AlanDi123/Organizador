import logging
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import filedialog
import traceback
from typing import Self
from PIL import Image, ImageTk
import requests
from io import BytesIO
from ui.dolar_widget import DolarFloatingWidgetRealtime
from datetime import datetime, timedelta
import calendar
import locale
from ui.dashboard_financiero import DashboardFinanciero
import os
from ui.dashboard_financiero import DashboardFinanciero
from ui.presupuesto_frame import PresupuestoFrame
from model.ia_module import modulo_ia
from ui.frames.gastos_frame import GastosFrame
from ui.frames.ingresos_frame import IngresosFrame
from model.gastos import calcular_total_gastos
from model.ingresos import calcular_total_ingresos
from model.data_manager import cargar_datos, eliminar_todos_datos, sincronizar_historiales

class AppController:
    def __init__(self, root):
        self.root = root
        self.modo_noche = False
        
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
        
        # Definir colores y estilos en tema rosa
        self.colores = {
            'claro': {
                'fondo': '#fff0f5',           # Rosa muy claro (Lavender blush)
                'panel': '#ffffff',           # Blanco
                'acento': '#ff69b4',          # Rosa intenso (Hot pink)
                'acento_oscuro': '#db7093',   # Rosa oscuro (Pale violet red)
                'texto': '#4b0082',           # Indigo (para texto)
                'texto_suave': '#c71585',     # Rosa medio (Medium violet red)
                'borde': '#ffe4e1',           # Rosa muy claro (Misty rose)
                'exito': '#98fb98',           # Verde claro (Pale green)
                'alerta': '#ff6347',          # Tomate (Tomato)
                'destacado': '#ffd700'        # Amarillo (Gold)
            },
            'oscuro': {
                'fondo': '#4b0082',           # Indigo
                'panel': '#800080',           # Púrpura
                'acento': '#ff69b4',          # Rosa intenso (Hot pink)
                'acento_oscuro': '#db7093',   # Rosa oscuro (Pale violet red)
                'texto': '#fff0f5',           # Rosa muy claro (Lavender blush)
                'texto_suave': '#ffc0cb',     # Rosa claro (Pink)
                'borde': '#c71585',           # Rosa medio (Medium violet red)
                'exito': '#98fb98',           # Verde claro (Pale green)
                'alerta': '#ff6347',          # Tomate (Tomato)
                'destacado': '#ffd700'        # Amarillo (Gold)
            }
        }
        
        # Cargar imagen de fondo con gatitos
        self.cargar_imagen_fondo()
        
        # Configurar el estilo ttk
        self.configurar_estilo()
        
        # Establecer fondo inicial con imagen
        self.aplicar_fondo()
        
        # Crear marco principal para contener todo
        self.main_frame = tk.Frame(self.root, bg=self.colores['claro']['fondo'], padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear título
        self.crear_titulo()
        
        # Crear botón de modo noche
        self.crear_boton_modo()
        
        # Crear contenedor para los paneles
        self.panels_frame = tk.Frame(self.main_frame, bg=self.colores['claro']['fondo'])
        self.panels_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Crear paneles lado a lado con bordes redondeados
        self.left_panel = tk.Frame(
            self.panels_frame, 
            bg=self.colores['claro']['fondo'], 
            padx=10
        )
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_panel = tk.Frame(
            self.panels_frame, 
            bg=self.colores['claro']['fondo'], 
            padx=10
        )
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        try:
            # Crear marcos para gastos e ingresos
            self.frame_gastos = GastosFrame(self.left_panel, self)
            self.frame_gastos.pack(fill=tk.BOTH, expand=True)
            
            self.frame_ingresos = IngresosFrame(self.right_panel, self)
            self.frame_ingresos.pack(fill=tk.BOTH, expand=True)
            
            # Panel inferior para botones de acción
            self.bottom_panel = tk.Frame(self.main_frame, bg=self.colores['claro']['fondo'], pady=10)
            self.bottom_panel.pack(fill=tk.X)
            
            # Crear botones para el panel inferior
            self.crear_boton_balance()
            self.crear_boton_borrar_todo()
        except Exception as e:
            print(f"Error durante la inicialización de componentes: {e}")
            messagebox.showerror("Error de inicialización", f"Ocurrió un error: {e}")


    

        # Crear botones para las funcionalidades de IA
        self.crear_boton_dashboard()
        self.crear_boton_presupuesto()
    
        # Crear menú principal
        self.menu_principal = tk.Menu(self.root)
        self.root.config(menu=self.menu_principal)

        # Menú Archivo
        self.menu_archivo = tk.Menu(self.menu_principal, tearoff=0)
        self.menu_principal.add_cascade(label="Archivo", menu=self.menu_archivo)

        # Añadir opción para importar datos
        self.menu_archivo.add_command(
            label="Importar datos de versión anterior", 
            command=self.importar_datos_version_anterior
        )

        # Añadir otras opciones al menú archivo
        self.menu_archivo.add_separator()
        self.menu_archivo.add_command(label="Salir", command=self.root.quit)

        # Crear botón para el widget del dólar
        self.crear_boton_dolar()
        
        # Forzar actualización de UI después de inicialización
        self.root.update_idletasks()

    def importar_datos_version_anterior(self):
        """Muestra un diálogo para importar datos de una versión anterior"""
        
        # Configurar logger
        logger = logging.getLogger('app_controller')
        
        try:
            # Importar nuestras funciones
            from model.db_migration import extract_data_from_old_version, backup_database
            
            # Crear nuevo importador simplificado inline
            def importar_datos_simples(gastos_list, ingresos_list):
                """Versión simplificada del importador"""
                import sqlite3
                from datetime import datetime
                
                # Usar conexión directa a la base de datos para evitar problemas de hilos
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'finanzas.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                gastos_ok = 0
                ingresos_ok = 0
                
                try:
                    # Iniciar transacción
                    conn.execute("BEGIN TRANSACTION")
                    
                    # Verificar gastos existentes para evitar duplicados EXACTOS
                    cursor.execute("SELECT id, nombre, fecha, monto FROM gastos")
                    gastos_existentes = set()
                    for row in cursor.fetchall():
                        # Guardamos la combinación nombre, fecha Y monto para detectar duplicados exactos
                        gastos_existentes.add((row[1], row[2], row[3]))
                    
                    # Para ingresos mantenemos la verificación simple
                    cursor.execute("SELECT id, concepto, fecha FROM ingresos")
                    ingresos_existentes = {(row[1], row[2]): row[0] for row in cursor.fetchall()}
                    
                    # Verificar la estructura actual de las tablas
                    cursor.execute("PRAGMA table_info(ingresos)")
                    columnas_ingresos = [row[1] for row in cursor.fetchall()]
                    print(f"Columnas en tabla ingresos: {columnas_ingresos}")
                    
                    # Importar gastos con verificación mejorada
                    for gasto in gastos_list:
                        try:
                            # Extraer valores básicos
                            nombre = str(gasto[1]) if len(gasto) > 1 else "Gasto importado"
                            monto = float(gasto[2]) if len(gasto) > 2 and gasto[2] else 0.0
                            recurrente = int(gasto[3]) if len(gasto) > 3 and gasto[3] else 0
                            fecha = str(gasto[4]) if len(gasto) > 4 and gasto[4] else datetime.now().strftime("%Y-%m-%d")
                            
                            # Omitir gastos con monto cero o nulo
                            if monto <= 0:
                                print(f"Omitiendo gasto con monto cero/nulo: {nombre} - {fecha}")
                                continue
                            
                            # VERIFICACIÓN MEJORADA: Solo comprobar duplicados EXACTOS
                            if (nombre, fecha, monto) in gastos_existentes:
                                print(f"Gasto duplicado exacto: {nombre} - {fecha} - ${monto:.2f}, omitiendo...")
                                continue
                            
                            # Insertar el gasto
                            cursor.execute("""
                                INSERT INTO gastos (nombre, monto, recurrente, fecha, fecha_creacion)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                nombre, monto, recurrente, fecha, 
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ))
                            
                            gastos_ok += 1
                        except Exception as e:
                            print(f"Error al importar gasto: {e}")
                            continue
                    
                    # Importar ingresos (sin cambios)
                    for ingreso in ingresos_list:
                        try:
                            # Extraer valores básicos
                            concepto = str(ingreso[1]) if len(ingreso) > 1 else "Ingreso importado"
                            monto = float(ingreso[2]) if len(ingreso) > 2 and ingreso[2] else 0.0
                            fecha = str(ingreso[3]) if len(ingreso) > 3 and ingreso[3] else datetime.now().strftime("%Y-%m-%d")
                            
                            # Omitir ingresos con monto cero o nulo
                            if monto <= 0:
                                print(f"Omitiendo ingreso con monto cero/nulo: {concepto} - {fecha}")
                                continue
                            
                            # Verificar si ya existe este ingreso
                            if (concepto, fecha) in ingresos_existentes:
                                print(f"Ingreso ya existe: {concepto} - {fecha}, omitiendo...")
                                continue
                            
                            # Verificar si existe columna recurrente
                            if 'recurrente' in columnas_ingresos:
                                recurrente = int(ingreso[4]) if len(ingreso) > 4 and ingreso[4] else 0
                                cursor.execute("""
                                    INSERT INTO ingresos (concepto, monto, fecha, recurrente, fecha_creacion)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (
                                    concepto, monto, fecha, recurrente, 
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ))
                            else:
                                # Si no existe la columna recurrente, omitirla
                                cursor.execute("""
                                    INSERT INTO ingresos (concepto, monto, fecha, fecha_creacion)
                                    VALUES (?, ?, ?, ?)
                                """, (
                                    concepto, monto, fecha,
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ))
                            
                            ingresos_ok += 1
                        except Exception as e:
                            print(f"Error al importar ingreso: {e}")
                            continue
                    
                    # Confirmar cambios
                    conn.commit()
                    print(f"Importación completada: {gastos_ok} gastos, {ingresos_ok} ingresos")
                    
                    return (gastos_ok, ingresos_ok)
                except Exception as e:
                    # Revertir en caso de error
                    conn.rollback()
                    print(f"Error durante la importación: {e}")
                    raise
                finally:
                    # Cerrar la conexión
                    conn.close()
            
            # Mostrar diálogo para seleccionar archivo
            archivo = filedialog.askopenfilename(
                title="Seleccionar base de datos anterior",
                filetypes=[("Base de datos SQLite", "*.db"), ("Todos los archivos", "*.*")]
            )
            
            if not archivo:
                return  # El usuario canceló
            
            # Confirmar la operación
            if not messagebox.askyesno(
                "Confirmar importación", 
                "¿Está seguro de importar datos de esta base de datos?\n"
                "Se realizará un respaldo de sus datos actuales antes de continuar."
            ):
                return
            
            # Crear backup de seguridad
            if not backup_database():
                messagebox.showerror(
                    "Error", 
                    "No se pudo crear un respaldo de seguridad. Operación cancelada."
                )
                return
            
            # Extraer datos de la versión antigua (importante: siempre inicializar 'datos')
            datos = extract_data_from_old_version(archivo)
            
            # Imprimir info para depuración
            if datos:
                print(f"Gastos encontrados: {len(datos['gastos'])}")
                print(f"Ingresos encontrados: {len(datos['ingresos'])}")
            
            # Verificar si hay datos para importar
            if not datos or (not datos['gastos'] and not datos['ingresos']):
                messagebox.showinfo(
                    "Sin datos", 
                    "No se encontraron datos para importar en la base de datos seleccionada."
                )
                return
            
            # Realizar la importación con nuestra función simplificada
            gastos_ok, ingresos_ok = importar_datos_simples(datos['gastos'], datos['ingresos'])
            
            # Mostrar resultado
            messagebox.showinfo(
                "Importación exitosa", 
                f"Se importaron {gastos_ok} gastos y {ingresos_ok} ingresos."
            )
            
            # Reiniciar la aplicación para reflejar los cambios
            if messagebox.askyesno(
                "Actualización completada", 
                "Los datos se han importado correctamente. ¿Desea reiniciar la aplicación para aplicar los cambios?"
            ):
                self.reiniciar_aplicacion()
                
        except Exception as e:
            # Capturar cualquier excepción y mostrar un mensaje de error
            error_details = traceback.format_exc()
            print(f"Error detallado: {error_details}")
            messagebox.showerror("Error", f"Error al importar datos: {str(e)}")

    def reiniciar_aplicacion(self):
        """Reinicia la aplicación para aplicar cambios"""
               
        try:
            # Cerrar ventanas y liberar recursos
            self.root.destroy()
            
            # Reiniciar la aplicación
            python = sys.executable
            os.execl(python, python, *sys.argv)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reiniciar la aplicación: {str(e)}")

    def cargar_imagen_fondo(self):
        """Carga una imagen de fondo con gatitos"""
        try:
            # Opción 1: Cargar desde una URL (Internet requerido)
            # url_imagen = "https://ejemplo.com/imagen_gatitos.jpg"
            # response = requests.get(url_imagen)
            # img_data = BytesIO(response.content)
            # self.bg_image = Image.open(img_data)
            
            # Opción 2: Intentar cargar una imagen local en la carpeta del proyecto
            # Buscar en la carpeta "assets" o directamente en la raíz
            rutas_posibles = [
                "assets/background_cats.png",
                "assets/background_cats.jpg",
                "background_cats.png",
                "background_cats.jpg"
            ]
            
            imagen_encontrada = False
            for ruta in rutas_posibles:
                if os.path.exists(ruta):
                    self.bg_image = Image.open(ruta)
                    imagen_encontrada = True
                    break
            
            # Si no se encuentra ninguna imagen, usar un color de fondo simple
            if not imagen_encontrada:
                self.bg_image = None
                print("No se encontró imagen de fondo. Se usará color sólido.")
        except Exception as e:
            print(f"Error al cargar imagen de fondo: {e}")
            self.bg_image = None

    def aplicar_fondo(self):
        """Aplica la imagen de fondo o un color sólido si no hay imagen"""
        try:
            if hasattr(self, 'bg_image') and self.bg_image:
                # Redimensionar la imagen al tamaño de la ventana
                width = self.root.winfo_width()
                height = self.root.winfo_height()
                
                # Si la ventana no tiene tamaño aún, usar un tamaño predeterminado
                if width <= 1 or height <= 1:
                    width, height = 1200, 800
                
                # Redimensionar la imagen manteniendo proporciones
                img_resized = self.bg_image.resize((width, height), Image.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(img_resized)
                
                # Crear un canvas para la imagen de fondo
                if not hasattr(self, 'bg_canvas') or not self.bg_canvas:
                    self.bg_canvas = tk.Canvas(self.root, highlightthickness=0)
                    self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Actualizar el canvas después de colocarlo
                self.root.update_idletasks()
                
                # Manera correcta de asegurar que el canvas está detrás de todo
                for widget in self.root.winfo_children():
                    if widget != self.bg_canvas:
                        widget.lift()
                
                # Configurar la opacidad para que no afecte la visibilidad
                self.bg_canvas.delete("all")
                # Añadir un filtro semitransparente para mejorar la legibilidad
                modo = 'oscuro' if self.modo_noche else 'claro'
                color_filtro = self.colores[modo]['fondo']
                self.bg_canvas.create_image(0, 0, image=self.bg_photo, anchor=tk.NW)
                self.bg_canvas.create_rectangle(0, 0, width, height, fill=color_filtro, 
                                            stipple="gray50", outline="")
            else:
                # Usar color sólido si no hay imagen
                modo = 'oscuro' if self.modo_noche else 'claro'
                color = self.colores[modo]['fondo']
                self.root.configure(bg=color)
                if hasattr(self, 'bg_canvas') and self.bg_canvas:
                    self.bg_canvas.delete("all")
                    self.bg_canvas.configure(bg=color)
                    
            # Forzar actualización de la interfaz
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error al aplicar fondo: {e}")
            # Fallback a color sólido si hay error
            modo = 'oscuro' if self.modo_noche else 'claro'
            self.root.configure(bg=self.colores[modo]['fondo'])

    def configurar_estilo(self):
        # Configurar estilos para ttk widgets con tema rosa
        self.estilo = ttk.Style()
        
        # Configuración general de widgets
        self.estilo.configure('TButton', font=('Comic Sans MS', 10), relief=tk.RAISED)
        self.estilo.configure('TEntry', font=('Comic Sans MS', 10))
        self.estilo.configure('TCombobox', font=('Comic Sans MS', 10))
        self.estilo.configure('TCheckbutton', font=('Comic Sans MS', 10))
        
        # Configurar colores para tema normal
        self.estilo.configure('TFrame', background=self.colores['claro']['panel'])
        self.estilo.map('TButton',
            background=[('active', self.colores['claro']['acento_oscuro']),
                        ('!active', self.colores['claro']['acento'])],
            foreground=[('active', 'white'), ('!active', 'white')]
        )
        
    def crear_titulo(self):
        # Marco para el título con línea decorativa
        title_frame = tk.Frame(self.main_frame, bg=self.colores['claro']['fondo'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Título con emoji decorativo
        self.label_titulo = tk.Label(
            title_frame, 
            text="✨ Organizador de Gastos e Ingresos ✨", 
            font=("Comic Sans MS", 22, "bold"), 
            fg=self.colores['claro']['acento'], 
            bg=self.colores['claro']['fondo']
        )
        self.label_titulo.pack(pady=(10, 5))
        
        # Línea divisoria decorativa
        separator = ttk.Separator(title_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 10))
    
    def crear_boton_modo(self):
        # Crear un botón redondeado para cambiar el modo
        self.btn_toggle_modo = tk.Button(
            self.root, 
            text="☀️ / 🌙", 
            command=self.toggle_modo, 
            relief=tk.RAISED,
            bg=self.colores['claro']['acento'],
            fg="white",
            font=("Comic Sans MS", 12),
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0  # Eliminar borde
        )
        self.btn_toggle_modo.place(x=10, y=10)
        
        # Hacer el botón redondeado
        self.redondear_widget(self.btn_toggle_modo)
    
    def crear_boton_balance(self):
        self.btn_mostrar_balance = tk.Button(
            self.bottom_panel, 
            text="📊 Mostrar Balance Total", 
            command=self.mostrar_balance_interfaz, 
            font=("Comic Sans MS", 11, "bold"), 
            bg=self.colores['claro']['acento'],
            fg="white",
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0  # Eliminar borde
        )
        self.btn_mostrar_balance.pack(side=tk.LEFT, padx=10)
        
        # Hacer el botón redondeado
        self.redondear_widget(self.btn_mostrar_balance)

    # Modificar el método crear_boton_dolar para usar la nueva implementación
    def crear_boton_dolar(self):
        """Crea el botón para mostrar el widget del dólar"""
        self.dolar_widget = DolarFloatingWidgetRealtime(self)
        
        self.btn_mostrar_dolar = tk.Button(
            self.bottom_panel, 
            text="💵 Dólar HOY", 
            command=self.mostrar_widget_dolar, 
            font=("Comic Sans MS", 11, "bold"), 
            bg=self.colores['claro']['acento_oscuro'],
            fg="white",
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_mostrar_dolar.pack(side=tk.LEFT, padx=10)
        self.redondear_widget(self.btn_mostrar_dolar)
        
    def mostrar_widget_dolar(self):
        """Muestra el widget de cotización del dólar"""
        try:
            self.dolar_widget.mostrar_widget()
        except Exception as e:
            print(f"Error al mostrar widget del dólar: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el widget del dólar: {e}")
    
    def crear_boton_borrar_todo(self):
        self.btn_borrar_todo = tk.Button(
            self.bottom_panel, 
            text="🗑️ Borrar Todo", 
            command=self.confirmar_borrar_todo, 
            font=("Comic Sans MS", 11, "bold"), 
            bg=self.colores['claro']['alerta'],
            fg="white",
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0  # Eliminar borde
        )
        self.btn_borrar_todo.pack(side=tk.RIGHT, padx=10)
        
        # Hacer el botón redondeado
        self.redondear_widget(self.btn_borrar_todo)
        
    def redondear_widget(self, widget):
        """Intenta redondear los bordes de un widget (funciona en algunos sistemas)"""
        try:
            # Intento de añadir esquinas redondeadas (funciona en algunos sistemas)
            widget.config(relief=tk.FLAT)
            widget.config(borderwidth=0)
            
            # En Windows, esta opción puede no funcionar según la versión de Tkinter
            if hasattr(widget, 'config') and callable(getattr(widget.config, '__call__', None)):
                widget.config(highlightthickness=0)
        except Exception as e:
            print(f"No se pudieron redondear los bordes: {e}")
    
    def toggle_modo(self):
        """Cambia entre el modo claro y oscuro y actualiza la interfaz"""
        try:
            # Cambiar el estado del modo
            self.modo_noche = not self.modo_noche
            
            # Determinar qué esquema de colores usar
            modo = 'oscuro' if self.modo_noche else 'claro'
            colores = self.colores[modo]
            
            # Actualizar el fondo con la imagen o color
            self.aplicar_fondo()
            
            # Verificar y actualizar cada componente
            if hasattr(self, 'main_frame'):
                self.main_frame.config(bg=colores['fondo'])
            
            if hasattr(self, 'panels_frame'):
                self.panels_frame.config(bg=colores['fondo'])
            
            if hasattr(self, 'left_panel'):
                self.left_panel.config(bg=colores['fondo'])
            
            if hasattr(self, 'right_panel'):
                self.right_panel.config(bg=colores['fondo'])
            
            if hasattr(self, 'bottom_panel'):
                self.bottom_panel.config(bg=colores['fondo'])
            
            # Actualizar el título
            if hasattr(self, 'label_titulo'):
                self.label_titulo.config(bg=colores['fondo'], fg=colores['acento'])
            
            # Actualizar el botón de modo
            if hasattr(self, 'btn_toggle_modo'):
                self.btn_toggle_modo.config(
                    bg=colores['acento'],
                    fg="white",
                    text="🌙" if not self.modo_noche else "☀️"
                )
            
            # Actualizar botones inferiores
            if hasattr(self, 'btn_mostrar_balance'):
                self.btn_mostrar_balance.config(bg=colores['acento'])
            
            if hasattr(self, 'btn_borrar_todo'):
                self.btn_borrar_todo.config(bg=colores['alerta'])
            
            # Actualizar frames de gastos e ingresos de manera segura
            # Esto evita excepciones al configurar los widgets DateEntry
            try:
                if hasattr(self, 'frame_gastos') and hasattr(self.frame_gastos, 'actualizar_modo'):
                    self.frame_gastos.actualizar_modo(modo)
            except Exception as e:
                print(f"Error al actualizar frame_gastos: {e}")
                # Continuar a pesar del error
            
            try:
                if hasattr(self, 'frame_ingresos') and hasattr(self.frame_ingresos, 'actualizar_modo'):
                    self.frame_ingresos.actualizar_modo(modo)
            except Exception as e:
                print(f"Error al actualizar frame_ingresos: {e}")
                # Continuar a pesar del error
            
            # Asegurar que los widgets principales permanezcan visibles
            if hasattr(self, 'main_frame'):
                self.main_frame.lift()
            
            # Forzar actualización de la interfaz
            self.root.update_idletasks()
        
        except Exception as e:
            print(f"Error al cambiar modo: {e}")
            messagebox.showerror("Error", f"No se pudo cambiar el modo: {e}")
    
    def mostrar_balance_interfaz(self):
        """Muestra la ventana de balance con los totales de gastos e ingresos y recomendaciones"""
        try:
            # Obtener los totales
            total_gastos = calcular_total_gastos()
            total_ingresos = calcular_total_ingresos()
            balance = total_ingresos - total_gastos
            
            # Colores según el modo actual
            modo = 'oscuro' if self.modo_noche else 'claro'
            colores = self.colores[modo]

            # Crear ventana emergente para el balance
            ventana = tk.Toplevel(self.root)
            ventana.title("Balance Total y Recomendaciones")
            ventana.geometry("900x450")  # Ventana más ancha para acomodar las recomendaciones
            ventana.configure(bg=colores['panel'])
            
            # Centrar la ventana
            ventana.withdraw()  # Ocultar ventana mientras se configura
            ventana.update_idletasks()
            ancho = ventana.winfo_width()
            alto = ventana.winfo_height()
            x = (ventana.winfo_screenwidth() // 2) - (ancho // 2)
            y = (ventana.winfo_screenheight() // 2) - (alto // 2)
            ventana.geometry('{}x{}+{}+{}'.format(ancho, alto, x, y))
            ventana.deiconify()  # Mostrar ventana ya configurada
            
            # Título de la ventana
            tk.Label(
                ventana, 
                text="✨ Resumen Financiero y Recomendaciones ✨", 
                font=("Comic Sans MS", 18, "bold"), 
                fg=colores['acento'],
                bg=colores['panel']
            ).pack(pady=(20, 10))
            
            # Separador debajo del título
            ttk.Separator(ventana, orient='horizontal').pack(fill=tk.X, padx=50, pady=10)
            
            # Panel principal dividido en dos columnas
            panel_principal = tk.Frame(ventana, bg=colores['panel'])
            panel_principal.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Panel izquierdo - Balance
            panel_balance = tk.Frame(panel_principal, bg=colores['panel'], padx=15, pady=15)
            panel_balance.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Panel derecho - Recomendaciones
            panel_recomendacion = tk.Frame(panel_principal, bg=colores['panel'], padx=15, pady=15)
            panel_recomendacion.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # Título para el panel de balance
            tk.Label(
                panel_balance, 
                text="Balance", 
                font=("Comic Sans MS", 14, "bold"), 
                fg=colores['acento'],
                bg=colores['panel']
            ).pack(anchor=tk.W, pady=(0, 10))
            
            # Estilo para las etiquetas
            estilo_etiqueta = {"font": ("Comic Sans MS", 12), "bg": colores['panel'], "fg": colores['texto']}
            estilo_valor = {"font": ("Comic Sans MS", 12, "bold"), "bg": colores['panel']}
            
            # Panel de info para el balance
            panel_info = tk.Frame(panel_balance, bg=colores['panel'])
            panel_info.pack(fill=tk.X, expand=True)
            
            # Ingresos
            tk.Label(panel_info, text="Total de Ingresos:", **estilo_etiqueta).grid(row=0, column=0, sticky=tk.W, pady=8)
            tk.Label(panel_info, text=f"${total_ingresos:.2f}", fg=colores['exito'], **estilo_valor).grid(row=0, column=1, sticky=tk.E, pady=8)
            
            # Gastos
            tk.Label(panel_info, text="Total de Gastos:", **estilo_etiqueta).grid(row=1, column=0, sticky=tk.W, pady=8)
            tk.Label(panel_info, text=f"${total_gastos:.2f}", fg=colores['alerta'], **estilo_valor).grid(row=1, column=1, sticky=tk.E, pady=8)
            
            # Línea separadora
            ttk.Separator(panel_info, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)
            
            # Balance final
            tk.Label(panel_info, text="Balance Final:", font=("Comic Sans MS", 14, "bold"), bg=colores['panel'], fg=colores['texto']).grid(row=3, column=0, sticky=tk.W, pady=12)
            
            # Color del balance según sea positivo o negativo
            color_balance = colores['exito'] if balance >= 0 else colores['alerta']
            tk.Label(panel_info, text=f"${balance:.2f}", font=("Comic Sans MS", 14, "bold"), bg=colores['panel'], fg=color_balance).grid(row=3, column=1, sticky=tk.E, pady=12)
            
            # Mensaje según el balance
            mensaje = "¡Bien hecho! Tus finanzas están en positivo. 🌸" if balance >= 0 else "Atención: Tus gastos superan a tus ingresos. 😿"
            tk.Label(panel_info, text=mensaje, font=("Comic Sans MS", 10, "italic"), bg=colores['panel'], fg=colores['texto_suave']).grid(row=4, column=0, columnspan=2, pady=10)
            
            # Configurar el grid
            panel_info.grid_columnconfigure(0, weight=1)
            panel_info.grid_columnconfigure(1, weight=1)
            
            # ===== SECCIÓN DE RECOMENDACIONES =====
            
            # Título para panel de recomendaciones
            tk.Label(
                panel_recomendacion, 
                text="Recomendaciones 💡", 
                font=("Comic Sans MS", 14, "bold"), 
                fg=colores['destacado'],
                bg=colores['panel']
            ).pack(anchor=tk.W, pady=(0, 10))
            
            # Frame para las recomendaciones
            recomendaciones_frame = tk.Frame(panel_recomendacion, bg=colores['panel'])
            recomendaciones_frame.pack(fill=tk.BOTH, expand=True)
            
            # Generar recomendaciones basadas en el balance
            if balance <= 0:
                # Recomendaciones para balance negativo o cero
                recomendaciones = [
                    ("Reducir gastos no esenciales", "Identifica gastos que puedas recortar temporalmente."),
                    ("Priorizar pagos urgentes", "Asegúrate de cubrir primero lo más importante."),
                    ("Evitar nuevas deudas", "Intenta no usar crédito hasta estabilizar tus finanzas.")
                ]
                color_titulo = colores['alerta']
            else:
                # Calcular porcentajes recomendados de ahorro
                ahorro = balance * 0.20  # 20% para ahorro
                emergencia = balance * 0.10  # 10% para fondo de emergencia
                inversion = balance * 0.15  # 15% para inversión
                gasto = balance * 0.55  # 55% para gastos de próxima quincena/mes
                
                if balance < 5000:  # Monto pequeño
                    recomendaciones = [
                        ("Ahorro para próxima quincena", f"Guarda ${gasto:.2f} para tus gastos futuros."),
                        ("Fondo de emergencia", f"Destina ${ahorro + emergencia:.2f} para emergencias."),
                        ("Pequeños ahorros", "Comienza a juntar para objetivos pequeños.")
                    ]
                elif balance < 15000:  # Monto medio
                    recomendaciones = [
                        ("Ahorro", f"Guarda ${ahorro:.2f} (20%) para objetivos a mediano plazo."),
                        ("Fondo de emergencia", f"Destina ${emergencia:.2f} (10%) para imprevistos."),
                        ("Inversiones seguras", f"Considera ${inversion:.2f} (15%) en plazos fijos."),
                        ("Gastos futuros", f"Reserva ${gasto:.2f} (55%) para la próxima quincena.")
                    ]
                else:  # Monto grande
                    recomendaciones = [
                        ("Ahorro", f"Guarda ${ahorro:.2f} (20%) para objetivos importantes."),
                        ("Fondo de emergencia", f"Destina ${emergencia:.2f} (10%) para imprevistos."),
                        ("Inversiones", f"Considera ${inversion:.2f} (15%) en bonos o fondos."),
                        ("Diversificación", "Divide tus inversiones en diferentes instrumentos."),
                        ("Gastos futuros", f"Reserva ${gasto:.2f} (55%) para la próxima quincena.")
                    ]
                color_titulo = colores['exito']
            
            # Mostrar recomendaciones
            for i, (titulo, detalle) in enumerate(recomendaciones):
                rec_frame = tk.Frame(recomendaciones_frame, bg=colores['panel'], padx=5, pady=5)
                rec_frame.pack(fill=tk.X, pady=5)
                
                # Título de la recomendación
                tk.Label(
                    rec_frame,
                    text=f"• {titulo}",
                    font=("Comic Sans MS", 11, "bold"),
                    fg=color_titulo,
                    bg=colores['panel'],
                    anchor=tk.W
                ).pack(fill=tk.X)
                
                # Detalle de la recomendación
                tk.Label(
                    rec_frame,
                    text=f"  {detalle}",
                    font=("Comic Sans MS", 10),
                    fg=colores['texto'],
                    bg=colores['panel'],
                    anchor=tk.W,
                    wraplength=350  # Para que el texto se ajuste al ancho
                ).pack(fill=tk.X)
            
            # Nota al pie
            if balance > 0:
                nota = "💫 Estas recomendaciones están basadas en tu balance actual.\nRecuerda que es importante personalizar tu estrategia financiera."
                tk.Label(
                    recomendaciones_frame,
                    text=nota,
                    font=("Comic Sans MS", 9, "italic"),
                    fg=colores['texto_suave'],
                    bg=colores['panel'],
                    justify=tk.LEFT
                ).pack(pady=(10, 0), anchor=tk.W)
            
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
            self.redondear_widget(btn_cerrar)
            
            # Forzar actualización de la interfaz
            ventana.update_idletasks()
            
            # Hacer la ventana modal
            ventana.transient(self.root)
            ventana.grab_set()
            
        except Exception as e:
            print(f"Error al mostrar balance: {e}")
            messagebox.showerror("Error", f"No se pudo mostrar el balance: {e}")

    def crear_boton_presupuesto(self):
        """Crea el botón para el presupuesto inteligente"""
        self.btn_mostrar_presupuesto = tk.Button(
            self.bottom_panel, 
            text="💰 Presupuesto IA", 
            command=self.mostrar_presupuesto_ai, 
            font=("Comic Sans MS", 11, "bold"), 
            bg=self.colores['claro']['acento_oscuro'],
            fg="white",
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_mostrar_presupuesto.pack(side=tk.LEFT, padx=10)
        self.redondear_widget(self.btn_mostrar_presupuesto)

    def mostrar_dashboard_ai(self):
        """Muestra el dashboard financiero inteligente"""
        try:
            dashboard = DashboardFinanciero(self.root, self)
        except Exception as e:
            print(f"Error al mostrar dashboard: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el dashboard: {e}")

    def mostrar_presupuesto_ai(self):
        """Muestra la interfaz de presupuesto inteligente"""
        try:
            presupuesto = PresupuestoFrame(self.root, self)
        except Exception as e:
            print(f"Error al mostrar presupuesto: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el presupuesto: {e}")

    def abrir_analisis_categoria(self, categoria):
        """Abre el análisis detallado de una categoría"""
        try:
            from ui.categoria_analisis import CategoriaAnalisis
            analisis = CategoriaAnalisis(self.root, self, categoria)
        except Exception as e:
            print(f"Error al abrir análisis de categoría: {e}")
            messagebox.showerror("Error", f"No se pudo abrir el análisis: {e}")
    
    def confirmar_borrar_todo(self):
        """Muestra un cuadro de diálogo para confirmar la eliminación de todos los datos excepto historial"""
        try:
            # Determinar colores según el modo actual
            modo = 'oscuro' if self.modo_noche else 'claro'
            colores = self.colores[modo]
            
            # Crear ventana de confirmación
            dialogo = tk.Toplevel(self.root)
            dialogo.title("Confirmar Eliminación")
            dialogo.geometry("450x280")
            dialogo.configure(bg=colores['panel'])
            dialogo.resizable(False, False)
            
            # Ocultar ventana mientras se configura
            dialogo.withdraw()
            
            # Centrar la ventana
            dialogo.update_idletasks()
            ancho = dialogo.winfo_width()
            alto = dialogo.winfo_height()
            x = (dialogo.winfo_screenwidth() // 2) - (ancho // 2)
            y = (dialogo.winfo_screenheight() // 2) - (alto // 2)
            dialogo.geometry('{}x{}+{}+{}'.format(ancho, alto, x, y))
            
            # Mostrar ventana ya configurada
            dialogo.deiconify()
            
            # Icono de advertencia
            tk.Label(
                dialogo, 
                text="⚠️", 
                font=("Comic Sans MS", 24), 
                bg=colores['panel'],
                fg=colores['alerta']
            ).pack(pady=(20, 0))
            
            # Mensaje de advertencia
            tk.Label(
                dialogo, 
                text="¿Estás seguro de que deseas eliminar los datos?", 
                font=("Comic Sans MS", 11, "bold"), 
                bg=colores['panel'],
                fg=colores['texto']
            ).pack(pady=(5, 0))
            
            tk.Label(
                dialogo, 
                text="Se borrarán todos los gastos e ingresos.", 
                font=("Comic Sans MS", 10), 
                bg=colores['panel'],
                fg=colores['texto_suave']
            ).pack(pady=(2, 0))
            
            # Mensaje sobre la preservación del historial
            tk.Label(
                dialogo, 
                text="El historial de conceptos y nombres de gastos se mantendrá.", 
                font=("Comic Sans MS", 10, "italic"), 
                bg=colores['panel'],
                fg=colores['acento']
            ).pack(pady=(2, 0))
            
            # Explicación adicional
            tk.Label(
                dialogo, 
                text="Esto permitirá que sigas viendo el historial de tus transacciones\ny podrás seleccionar gastos e ingresos previos en los menús desplegables.", 
                font=("Comic Sans MS", 9), 
                bg=colores['panel'],
                fg=colores['texto_suave'],
                justify=tk.CENTER
            ).pack(pady=(5, 15))
            
            # Frame para los botones
            botones_frame = tk.Frame(dialogo, bg=colores['panel'])
            botones_frame.pack(pady=(0, 20))
            
            # Función para eliminar los datos
            def borrar_datos():
                try:
                    # Asegurar que el historial está sincronizado antes de borrar
                    sincronizar_historiales()
                    
                    # Borrar todos los datos principales (el historial está en otra DB)
                    if eliminar_todos_datos():
                        messagebox.showinfo("Éxito", "Se han borrado todos los datos correctamente, manteniendo el historial de conceptos y gastos.")
                        
                        # Actualizar las interfaces
                        if hasattr(self, 'frame_gastos'):
                            try:
                                self.frame_gastos.nombres_gastos_historicos = self.frame_gastos.cargar_nombres_gastos_historicos()
                                self.frame_gastos.combo_gasto_nombre['values'] = self.frame_gastos.nombres_gastos_historicos
                            except Exception as e:
                                print(f"Error al actualizar combobox de gastos: {e}")
                        
                        if hasattr(self, 'frame_ingresos'):
                            try:
                                self.frame_ingresos.conceptos_historicos = self.frame_ingresos.cargar_conceptos_historicos()
                                self.frame_ingresos.combo_ingreso_concepto['values'] = self.frame_ingresos.conceptos_historicos
                            except Exception as e:
                                print(f"Error al actualizar combobox de ingresos: {e}")
                        
                        dialogo.destroy()
                    else:
                        messagebox.showerror("Error", "Ocurrió un error al intentar borrar los datos.")
                except Exception as e:
                    print(f"Error durante el borrado de datos: {e}")
                    messagebox.showerror("Error", f"Ocurrió un error: {e}")
            
            # Botones de confirmación
            btn_cancelar = tk.Button(
                botones_frame, 
                text="Cancelar", 
                command=dialogo.destroy, 
                font=("Comic Sans MS", 10), 
                bg=colores['borde'],
                fg=colores['texto'],
                padx=15,
                pady=5,
                relief=tk.FLAT,
                cursor="hand2",
                borderwidth=0
            )
            btn_cancelar.pack(side=tk.LEFT, padx=10)
            self.redondear_widget(btn_cancelar)
            
            btn_borrar = tk.Button(
                botones_frame, 
                text="Sí, Borrar", 
                command=borrar_datos, 
                font=("Comic Sans MS", 10, "bold"), 
                bg=colores['alerta'],
                fg="white",
                padx=15,
                pady=5,
                relief=tk.FLAT,
                cursor="hand2",
                borderwidth=0
            )
            btn_borrar.pack(side=tk.LEFT, padx=10)
            self.redondear_widget(btn_borrar)
            
            # Hacer la ventana modal
            dialogo.transient(self.root)
            dialogo.grab_set()
            
            # Forzar actualización de la interfaz
            dialogo.update_idletasks()
            
        except Exception as e:
            print(f"Error al mostrar diálogo de confirmación: {e}")
            messagebox.showerror("Error", f"No se pudo mostrar la ventana de confirmación: {e}")

            
    def calcular_fecha_proxima_quincena(self):
        """Calcula la fecha de la próxima quincena (día 15 o 1 del mes siguiente)"""
        try:
            # Obtener la fecha actual
            fecha_actual = datetime.now()
            dia_actual = fecha_actual.day
            
            # Determinar la fecha de la próxima quincena
            if dia_actual < 15:
                # Si estamos antes del 15, la próxima quincena es el 15 del mes actual
                return datetime(fecha_actual.year, fecha_actual.month, 15)
            else:
                # Si estamos después del 15, la próxima quincena es el 1 del siguiente mes
                if fecha_actual.month == 12:
                    return datetime(fecha_actual.year + 1, 1, 1)
                else:
                    return datetime(fecha_actual.year, fecha_actual.month + 1, 1)
        except Exception as e:
            print(f"Error al calcular fecha de quincena: {e}")
            # En caso de error, devolver la fecha actual + 15 días como fallback
            return datetime.now() + timedelta(days=15)
    
    def calcular_fecha_ingreso_semana_vencida(self):
        """Calcula la fecha de ingreso (una semana después de la quincena)"""
        try:
            # Obtener la fecha de la próxima quincena
            fecha_quincena = self.calcular_fecha_proxima_quincena()
            
            # Sumar una semana
            fecha_ingreso = fecha_quincena + timedelta(days=7)
            
            return fecha_ingreso
        except Exception as e:
            print(f"Error al calcular fecha de ingreso: {e}")
            # En caso de error, devolver la fecha actual + 22 días como fallback
            return datetime.now() + timedelta(days=22)
        
    def crear_boton_dashboard(self):
        """Crea el botón para abrir el dashboard financiero IA"""
        self.btn_mostrar_dashboard = tk.Button(
            self.bottom_panel, 
            text="🧠 Dashboard IA", 
            command=self.mostrar_dashboard_ai, 
            font=("Comic Sans MS", 11, "bold"), 
            bg=self.colores['claro']['acento_oscuro'],
            fg="white",
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_mostrar_dashboard.pack(side=tk.LEFT, padx=10)
        self.redondear_widget(self.btn_mostrar_dashboard)