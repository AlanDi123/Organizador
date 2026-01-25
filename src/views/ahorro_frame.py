import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import sqlite3
import os
import threading

class AhorroFrame(tk.Frame):
    """Frame para gestionar ahorros independientes del sistema de gastos e ingresos"""
    
    def __init__(self, parent, controller):
        self.controller = controller
        colores = controller.colores['claro']
        
        super().__init__(
            parent, 
            bg=colores['panel'],
            highlightthickness=1,
            padx=15, 
            pady=15,
            relief=tk.RAISED,
            bd=0
        )
        
        # Base de datos de ahorros
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'ahorros.db')
        self.inicializar_db()
        
        # Crear widgets
        self.crear_widgets()
    
    def inicializar_db(self):
        """Inicializa la base de datos de ahorros"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Crear tabla de ahorros si no existe
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ahorros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descripcion TEXT NOT NULL,
                    monto REAL NOT NULL,
                    fecha TEXT NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error al inicializar BD de ahorros: {e}")
    
    def crear_widgets(self):
        """Crea los widgets del frame de ahorros"""
        colores = self.controller.colores['claro']
        
        # Título de la sección
        title_frame = tk.Frame(self, bg=colores['panel'])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.label_ahorro = tk.Label(
            title_frame, 
            text="🏦 Banco de Ahorros", 
            font=("Comic Sans MS", 14, "bold"), 
            fg=colores['texto'],
            bg=colores['panel']
        )
        self.label_ahorro.pack(anchor=tk.W)
        
        # Separador
        separator = ttk.Separator(title_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(5, 0))
        
        # Crear frame para formulario
        form_frame = tk.Frame(self, bg=colores['panel'], pady=10)
        form_frame.pack(fill=tk.X)
        
        # Descripción del ahorro
        tk.Label(
            form_frame, 
            text="Descripción del ahorro:", 
            font=("Comic Sans MS", 12), 
            fg=colores['texto'],
            bg=colores['panel'],
            anchor=tk.W
        ).pack(fill=tk.X, pady=(10, 5))
        
        self.entry_descripcion = tk.Entry(
            form_frame, 
            font=("Comic Sans MS", 12),
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1
        )
        self.entry_descripcion.pack(fill=tk.X)
        
        # Monto del ahorro
        tk.Label(
            form_frame, 
            text="Monto ($):", 
            font=("Comic Sans MS", 12), 
            fg=colores['texto'],
            bg=colores['panel'],
            anchor=tk.W
        ).pack(fill=tk.X, pady=(10, 5))
        
        self.entry_monto = tk.Entry(
            form_frame, 
            font=("Comic Sans MS", 12),
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1
        )
        self.entry_monto.pack(fill=tk.X)
        
        # Vincular Enter para agregar
        self.entry_monto.bind('<Return>', self.agregar_ahorro_event)
        
        # Frame para botones
        buttons_frame = tk.Frame(self, bg=colores['panel'])
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Botón de agregar
        self.btn_agregar = tk.Button(
            buttons_frame, 
            text="➕ Agregar Ahorro", 
            command=self.agregar_ahorro, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['exito'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_agregar.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        # Botón de eliminar
        self.btn_eliminar = tk.Button(
            buttons_frame, 
            text="❌ Eliminar", 
            command=self.eliminar_ahorro, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['alerta'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_eliminar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Botón de mostrar ahorros
        self.btn_mostrar = tk.Button(
            buttons_frame, 
            text="📋 Mis Ahorros", 
            command=self.mostrar_ahorros, 
            font=("Comic Sans MS", 10, "bold"), 
            bg=colores['acento'],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            borderwidth=0
        )
        self.btn_mostrar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Frame para mostrar total
        total_frame = tk.Frame(self, bg=colores['borde'], padx=15, pady=10)
        total_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(
            total_frame,
            text="💰 Total Ahorrado:",
            font=("Comic Sans MS", 11, "bold"),
            fg=colores['texto'],
            bg=colores['borde']
        ).pack(side=tk.LEFT)
        
        self.lbl_total = tk.Label(
            total_frame,
            text="$0.00",
            font=("Comic Sans MS", 12, "bold"),
            fg=colores['exito'],
            bg=colores['borde']
        )
        self.lbl_total.pack(side=tk.LEFT, padx=(10, 0))
        
        # Actualizar total
        self.actualizar_total()
    
    def agregar_ahorro_event(self, event):
        """Evento cuando se presiona Enter"""
        self.agregar_ahorro()
    
    def eliminar_ahorro(self):
        """Elimina un ahorro de la BD"""
        descripcion = self.entry_descripcion.get().strip()
        
        if not descripcion:
            messagebox.showerror("Error", "Debes ingresar una descripción del ahorro a eliminar.")
            self.entry_descripcion.focus_set()
            return
        
        # Confirmar eliminación
        if messagebox.askyesno("Confirmar", f"¿Eliminar el ahorro '{descripcion}'? Esta acción no se puede deshacer."):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Buscar y eliminar ahorros con esa descripción
                cursor.execute('DELETE FROM ahorros WHERE descripcion = ?', (descripcion,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("Éxito", f"✅ Se eliminó el ahorro '{descripcion}'.")
                    
                    # Limpiar campos
                    self.entry_descripcion.delete(0, tk.END)
                    self.entry_monto.delete(0, tk.END)
                    self.entry_descripcion.focus_set()
                    
                    # Actualizar total
                    self.actualizar_total()
                else:
                    conn.close()
                    messagebox.showinfo("Información", f"No se encontró ningún ahorro con la descripción '{descripcion}'.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el ahorro: {e}")
    
    def agregar_ahorro(self):
        """Agrega un nuevo ahorro a la BD"""
        descripcion = self.entry_descripcion.get().strip()
        monto_str = self.entry_monto.get().strip()
        
        if not descripcion:
            messagebox.showerror("Error", "Debes ingresar una descripción para el ahorro.")
            self.entry_descripcion.focus_set()
            return
        
        try:
            monto = float(monto_str.replace(',', '.'))
            if monto <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor que cero.")
                self.entry_monto.focus_set()
                return
        except ValueError:
            messagebox.showerror("Error", "Monto inválido. Por favor, ingresa un número válido.")
            self.entry_monto.focus_set()
            return
        
        # Guardar en BD
        try:
            fecha = datetime.now().strftime("%Y-%m-%d")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ahorros (descripcion, monto, fecha)
                VALUES (?, ?, ?)
            ''', (descripcion, monto, fecha))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Éxito", f"✅ Se agregó ${monto:.2f} a tus ahorros.")
            
            # Limpiar campos
            self.entry_descripcion.delete(0, tk.END)
            self.entry_monto.delete(0, tk.END)
            self.entry_descripcion.focus_set()
            
            # Actualizar total
            self.actualizar_total()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el ahorro: {e}")
    
    def actualizar_total(self):
        """Actualiza el total de ahorros mostrado"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT SUM(monto) FROM ahorros')
            result = cursor.fetchone()
            total = result[0] if result[0] else 0
            
            conn.close()
            
            self.lbl_total.config(text=f"${total:,.2f}")
        except Exception as e:
            print(f"Error al actualizar total: {e}")
    
    def mostrar_ahorros(self):
        """Muestra una ventana con todos los ahorros"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, descripcion, monto, fecha FROM ahorros ORDER BY fecha DESC')
            ahorros = cursor.fetchall()
            conn.close()
            
            if not ahorros:
                messagebox.showinfo("Ahorros", "No hay ahorros registrados.")
                return
            
            # Crear ventana
            ventana = tk.Toplevel(self.controller.root)
            ventana.title("📋 Mis Ahorros")
            ventana.geometry("850x600")
            
            modo = 'oscuro' if self.controller.modo_noche else 'claro'
            colores = self.controller.colores[modo]
            ventana.configure(bg=colores['panel'])
            
            ventana.transient(self.controller.root)
            ventana.grab_set()
            
            # Título
            tk.Label(
                ventana,
                text="📋 Historial de Ahorros",
                font=("Comic Sans MS", 18, "bold"),
                fg=colores['acento'],
                bg=colores['panel']
            ).pack(pady=(20, 10))
            
            # Frame para la tabla
            tabla_frame = tk.Frame(ventana, bg=colores['panel'], padx=20, pady=10)
            tabla_frame.pack(fill=tk.BOTH, expand=True)
            
            # Instrucciones
            instrucciones_label = tk.Label(
                tabla_frame,
                text="💡 Selecciona ahorros con Ctrl+Click para eliminarlos",
                font=("Comic Sans MS", 11),
                fg=colores['texto_suave'],
                bg=colores['panel']
            )
            instrucciones_label.pack(anchor=tk.W, pady=(0, 10))
            
            # Crear Treeview
            columnas = ("id", "descripcion", "monto", "fecha")
            tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings", height=15)
            
            # Configurar columnas
            tree.heading("id", text="ID")
            tree.heading("descripcion", text="Descripción")
            tree.heading("monto", text="Monto ($)")
            tree.heading("fecha", text="Fecha")
            
            tree.column("id", width=40, anchor=tk.CENTER)
            tree.column("descripcion", width=280, anchor=tk.W)
            tree.column("monto", width=150, anchor=tk.E)
            tree.column("fecha", width=130, anchor=tk.CENTER)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Insertar datos
            total = 0
            for ahorro in ahorros:
                id_ahorro, desc, monto, fecha = ahorro
                tree.insert("", tk.END, values=(id_ahorro, desc, f"{monto:.2f}", fecha))
                total += monto
            
            # Frame para total
            total_frame = tk.Frame(ventana, bg=colores['panel'], padx=20, pady=10)
            total_frame.pack(fill=tk.X)
            
            tk.Label(
                total_frame,
                text="Total Ahorrado:",
                font=("Comic Sans MS", 12, "bold"),
                fg=colores['texto'],
                bg=colores['panel']
            ).pack(side=tk.LEFT)
            
            tk.Label(
                total_frame,
                text=f"${total:,.2f}",
                font=("Comic Sans MS", 12, "bold"),
                fg=colores['exito'],
                bg=colores['panel']
            ).pack(side=tk.LEFT, padx=(10, 0))
            
            # Frame para botones
            botones_frame = tk.Frame(ventana, bg=colores['panel'])
            botones_frame.pack(pady=(5, 20), fill=tk.X, padx=20)
            
            # Botón eliminar seleccionados
            def eliminar_seleccionados():
                seleccionados = tree.selection()
                if not seleccionados:
                    messagebox.showwarning("Atención", "Debes seleccionar al menos un ahorro para eliminar.")
                    return
                
                cantidad = len(seleccionados)
                if messagebox.askyesno("Confirmar", f"¿Eliminar {cantidad} ahorro(s)? Esta acción no se puede deshacer."):
                    try:
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        
                        for item in seleccionados:
                            valores = tree.item(item)['values']
                            ahorro_id = valores[0]
                            cursor.execute('DELETE FROM ahorros WHERE id = ?', (ahorro_id,))
                            tree.delete(item)
                        
                        conn.commit()
                        conn.close()
                        
                        messagebox.showinfo("Éxito", f"{cantidad} ahorro(s) eliminado(s).")
                        self.actualizar_total()
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al eliminar: {e}")
            
            tk.Button(
                botones_frame,
                text="🗑️ Eliminar Seleccionados",
                command=eliminar_seleccionados,
                font=("Comic Sans MS", 12),
                bg=colores['alerta'],
                fg="white",
                relief=tk.FLAT,
                padx=10,
                pady=5,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                botones_frame,
                text="Cerrar",
                command=ventana.destroy,
                font=("Comic Sans MS", 12),
                bg=colores['borde'],
                fg=colores['texto'],
                relief=tk.FLAT,
                padx=10,
                pady=5,
                cursor="hand2"
            ).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los ahorros: {e}")
