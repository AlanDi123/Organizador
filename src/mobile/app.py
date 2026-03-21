"""
Aplicación Móvil - KivyMD
Punto de entrada para la versión Android/iOS
"""

import os
import logging
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.list import OneLineAvatarListItem, IconLeftWidget

from src.core.services import GastosService, IngresosService, AuthService, PresupuestoService
from src.cloud.sync_engine import SyncEngine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrganizadorApp(MDApp):
    """Aplicación principal para móviles"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Organizador de Gastos"
        self.icon = 'assets/icon.png'
        
        # Servicios
        self.gastos_service = GastosService()
        self.ingresos_service = IngresosService()
        self.auth_service = AuthService()
        self.presupuesto_service = PresupuestoService()
        self.sync_engine = SyncEngine()
        
        # Estado
        self.user_logged = False
        self.current_balance = 0.0
    
    def build(self):
        """Construye la aplicación"""
        self.theme_cls.primary_palette = "Pink"
        self.theme_cls.accent_palette = "Purple"
        self.theme_cls.theme_style = "Light"
        
        # Configurar ventana
        Window.size = (360, 640)  # Tamaño default para testing
        Window.minimum_width, Window.minimum_height = 300, 500
        
        # Cargar KV
        self.load_kv_files()
        
        # Crear screen manager
        self.sm = MDScreenManager()
        self.setup_screens()
        
        # Crear navigation drawer
        self.setup_navigation_drawer()
        
        return self.sm
    
    def load_kv_files(self):
        """Carga archivos KV"""
        # En producción, cargar desde archivos .kv separados
        Builder.load_string(self.get_main_kv())
    
    def get_main_kv(self) -> str:
        """Retorna el KV principal embebido"""
        return '''
#:import NoTransition kivy.uix.screenmanager.NoTransition

MDScreenManager:
    transition: NoTransition()
    
    MDScreen:
        name: 'login'
        
        MDBoxLayout:
            orientation: 'vertical'
            padding: dp(20)
            spacing: dp(20)
            adaptive_height: True
            pos_hint: {'center_x': 0.5, 'center_y': 0.6}
            
            MDLabel:
                text: "💰 Organizador de Gastos"
                font_style: "H4"
                halign: "center"
                theme_text_color: "Primary"
            
            MDLabel:
                text: "Gestioná tus finanzas personales"
                font_style: "Subtitle1"
                halign: "center"
                theme_text_color: "Secondary"
            
            MDTextField:
                id: email_field
                hint_text: "Email"
                mode: "rectangle"
                size_hint_x: 1
                icon_left: "email"
            
            MDTextField:
                id: password_field
                hint_text: "Contraseña"
                password: True
                mode: "rectangle"
                size_hint_x: 1
                icon_left: "lock"
            
            MDRaisedButton:
                text: "Iniciar Sesión"
                size_hint_x: 1
                on_release: app.login()
            
            MDTextButton:
                text: "¿No tenés cuenta? Registrate"
                on_release: app.register()
    
    MDScreen:
        name: 'home'
        
        MDBoxLayout:
            orientation: 'vertical'
            
            MDTopAppBar:
                title: "Organizador"
                left_action_items: [["menu", lambda x: app.open_nav_drawer()]]
                right_action_items: [["sync", lambda x: app.sync_data()], ["dots-vertical", lambda x: app.show_menu()]]
                elevation: 2
            
            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                spacing: dp(10)
                
                MDCard:
                    orientation: 'vertical'
                    padding: dp(15)
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(150)
                    elevation: 2
                    
                    MDLabel:
                        text: "Balance Total"
                        font_style: "Subtitle1"
                        theme_text_color: "Secondary"
                        size_hint_y: None
                        height: self.texture_size[1]
                    
                    MDLabel:
                        id: balance_label
                        text: "$ 0.00"
                        font_style: "H4"
                        theme_text_color: "Primary"
                        halign: "center"
                        size_hint_y: None
                        height: self.texture_size[1]
                    
                    MDLabel:
                        id: last_sync_label
                        text: ""
                        font_style: "Caption"
                        theme_text_color: "Hint"
                        halign: "center"
                        size_hint_y: None
                        height: self.texture_size[1]
                
                MDBoxLayout:
                    size_hint_y: None
                    height: dp(100)
                    spacing: dp(10)
                    
                    MDCard:
                        orientation: 'vertical'
                        padding: dp(10)
                        elevation: 1
                        on_release: app.go_to_screen('gastos')
                        
                        MDIcon:
                            icon: "cart"
                            halign: "center"
                            font_size: dp(30)
                            theme_text_color: "Primary"
                        
                        MDLabel:
                            text: "Gastos"
                            halign: "center"
                            font_style: "Caption"
                    
                    MDCard:
                        orientation: 'vertical'
                        padding: dp(10)
                        elevation: 1
                        on_release: app.go_to_screen('ingresos')
                        
                        MDIcon:
                            icon: "cash"
                            halign: "center"
                            font_size: dp(30)
                            theme_text_color: "Primary"
                        
                        MDLabel:
                            text: "Ingresos"
                            halign: "center"
                            font_style: "Caption"
                    
                    MDCard:
                        orientation: 'vertical'
                        padding: dp(10)
                        elevation: 1
                        on_release: app.go_to_screen('dashboard')
                        
                        MDIcon:
                            icon: "chart-pie"
                            halign: "center"
                            font_size: dp(30)
                            theme_text_color: "Primary"
                        
                        MDLabel:
                            text: "Dashboard"
                            halign: "center"
                            font_style: "Caption"
                
                MDList:
                    id: recent_transactions
                    
                    OneLineAvatarListItem:
                        text: "Cargando transacciones..."
                        disabled: True
    
    MDScreen:
        name: 'gastos'
        
        MDBoxLayout:
            orientation: 'vertical'
            
            MDTopAppBar:
                title: "Gastos"
                left_action_items: [["arrow-left", lambda x: app.go_to_screen('home')]]
                right_action_items: [["plus", lambda x: app.add_gasto()]]
                elevation: 2
            
            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                spacing: dp(10)
                
                MDTextField:
                    id: gasto_nombre
                    hint_text: "Nombre del gasto"
                    mode: "rectangle"
                    icon_left: "label"
                
                MDTextField:
                    id: gasto_monto
                    hint_text: "Monto"
                    mode: "rectangle"
                    keyboard_type: 'decimal'
                    icon_left: "currency-usd"
                
                MDCheckbox:
                    id: gasto_recurrente
                    text: "Recurrente"
                    size_hint: None, None
                    size: dp(200), dp(48)
                
                MDRaisedButton:
                    text: "Agregar Gasto"
                    size_hint_x: 1
                    on_release: app.guardar_gasto()
                
                MDLabel:
                    text: "Historial de Gastos"
                    font_style: "H6"
                    padding: dp(10)
                
                ScrollView:
                    MDList:
                        id: gastos_list
    
    MDScreen:
        name: 'ingresos'
        
        MDBoxLayout:
            orientation: 'vertical'
            
            MDTopAppBar:
                title: "Ingresos"
                left_action_items: [["arrow-left", lambda x: app.go_to_screen('home')]]
                right_action_items: [["plus", lambda x: app.add_ingreso()]]
                elevation: 2
            
            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                spacing: dp(10)
                
                MDTextField:
                    id: ingreso_concepto
                    hint_text: "Concepto"
                    mode: "rectangle"
                    icon_left: "label"
                
                MDTextField:
                    id: ingreso_monto
                    hint_text: "Monto"
                    mode: "rectangle"
                    keyboard_type: 'decimal'
                    icon_left: "currency-usd"
                
                MDRaisedButton:
                    text: "Agregar Ingreso"
                    size_hint_x: 1
                    on_release: app.guardar_ingreso()
                
                MDLabel:
                    text: "Historial de Ingresos"
                    font_style: "H6"
                    padding: dp(10)
                
                ScrollView:
                    MDList:
                        id: ingresos_list
    
    MDScreen:
        name: 'dashboard'
        
        MDBoxLayout:
            orientation: 'vertical'
            
            MDTopAppBar:
                title: "Dashboard"
                left_action_items: [["arrow-left", lambda x: app.go_to_screen('home')]]
                elevation: 2
            
            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(10)
                spacing: dp(10)
                
                MDLabel:
                    text: "Próximamente..."
                    halign: "center"
                    pos_hint: {'center_y': 0.5}
'''
    
    def setup_screens(self):
        """Configura las pantallas"""
        # Las pantallas se definen en el KV
        pass
    
    def setup_navigation_drawer(self):
        """Configura el navigation drawer"""
        self.nav_drawer = MDNavigationDrawer()
        self.nav_drawer.set_state("close")
        
        # Header
        header = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            padding=(dp(20), dp(20))
        )
        
        from kivymd.uix.label import MDLabel
        header.add_widget(MDLabel(
            text="Usuario",
            font_style="H6",
            theme_text_color="Primary"
        ))
        header.add_widget(MDLabel(
            text="email@ejemplo.com",
            font_style="Caption",
            theme_text_color="Secondary"
        ))
        
        self.nav_drawer.add_widget(header)
        
        # Menu items
        from kivymd.uix.list import OneLineIconListItem, IconLeftWidget
        
        items = [
            ("home", "home", "Inicio"),
            ("gastos", "cart", "Gastos"),
            ("ingresos", "cash", "Ingresos"),
            ("dashboard", "chart-pie", "Dashboard"),
            ("settings", "cog", "Configuración"),
        ]
        
        for screen_name, icon, text in items:
            item = OneLineIconListItem(text=text, on_release=lambda x, s=screen_name: self.go_to_screen(s))
            item.add_widget(IconLeftWidget(icon=icon))
            self.nav_drawer.add_widget(item)
        
        # Logout
        logout_item = OneLineIconListItem(text="Cerrar Sesión", on_release=lambda x: self.logout())
        logout_item.add_widget(IconLeftWidget(icon="logout"))
        self.nav_drawer.add_widget(logout_item)
        
        self.sm.add_widget(self.nav_drawer)
    
    def on_start(self):
        """Se ejecuta al iniciar la app"""
        logger.info("App iniciada")
        self.check_auth_status()
    
    def check_auth_status(self):
        """Verifica estado de autenticación"""
        if self.auth_service.esta_autenticado():
            self.user_logged = True
            self.go_to_screen('home')
            self.update_balance()
        else:
            self.go_to_screen('login')
    
    def login(self):
        """Intenta iniciar sesión"""
        email = self.root.ids.email_field.text if hasattr(self.root, 'ids') and 'email_field' in self.root.ids else ""
        password = self.root.ids.password_field.text if hasattr(self.root, 'ids') and 'password_field' in self.root.ids else ""
        
        if not email or not password:
            self.show_snackbar("Completa email y contraseña")
            return
        
        if self.auth_service.login(email, password):
            self.user_logged = True
            self.show_snackbar("¡Bienvenido!")
            self.go_to_screen('home')
            self.update_balance()
        else:
            self.show_snackbar("Error de autenticación")
    
    def register(self):
        """Registra nuevo usuario"""
        # Navegar a pantalla de registro (implementar)
        self.show_snackbar("Registro - Próximamente")
    
    def logout(self):
        """Cierra sesión"""
        self.auth_service.logout()
        self.user_logged = False
        self.nav_drawer.set_state("close")
        self.go_to_screen('login')
        self.show_snackbar("Sesión cerrada")
    
    def go_to_screen(self, screen_name: str):
        """Navega a una pantalla"""
        if hasattr(self, 'sm'):
            self.sm.current = screen_name
        if hasattr(self, 'nav_drawer') and self.nav_drawer.get_state() == "open":
            self.nav_drawer.set_state("close")
    
    def open_nav_drawer(self):
        """Abre el navigation drawer"""
        if hasattr(self, 'nav_drawer'):
            self.nav_drawer.set_state("open")
    
    def show_snackbar(self, text: str):
        """Muestra un snackbar"""
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text=text).open()
    
    def update_balance(self):
        """Actualiza el balance mostrado"""
        try:
            total_gastos = self.gastos_service.calcular_total()
            total_ingresos = self.ingresos_service.calcular_total()
            self.current_balance = total_ingresos - total_gastos
            
            # Actualizar UI
            if hasattr(self.root, 'ids') and 'balance_label' in self.root.ids:
                self.root.ids.balance_label.text = f"$ {self.current_balance:,.2f}"
            
            # Actualizar último sync
            sync_status = self.sync_engine.get_sync_status()
            if sync_status.get('last_sync'):
                last_sync = sync_status['last_sync']
                if hasattr(self.root, 'ids') and 'last_sync_label' in self.root.ids:
                    self.root.ids.last_sync_label.text = f"Última sync: {last_sync}"
            
            # Cargar transacciones recientes
            self.load_recent_transactions()
            
        except Exception as e:
            logger.error(f"Error al actualizar balance: {e}")
    
    def load_recent_transactions(self):
        """Carga transacciones recientes en la lista"""
        try:
            # Limpiar lista
            if hasattr(self.root, 'ids') and 'recent_transactions' in self.root.ids:
                lista = self.root.ids.recent_transactions
                lista.clear_widgets()
                
                # Obtener últimos movimientos
                gastos = self.gastos_service.obtener_todos()[-5:]
                ingresos = self.ingresos_service.obtener_todos()[-5:]
                
                # Combinar y ordenar
                todos = []
                for g in gastos:
                    todos.append(('gasto', g))
                for i in ingresos:
                    todos.append(('ingreso', i))
                
                todos.sort(key=lambda x: x[1].fecha_creacion, reverse=True)
                
                # Agregar a la lista
                for tipo, item in todos[:10]:
                    from kivymd.uix.list import OneLineListItem, IconLeftWidget
                    icon = "cart" if tipo == 'gasto' else "cash"
                    color = "red" if tipo == 'gasto' else "green"
                    signo = "-" if tipo == 'gasto' else "+"
                    
                    list_item = OneLineListItem(
                        text=f"{item.nombre if tipo == 'gasto' else item.concepto} - ${item.monto:.2f}"
                    )
                    list_item.add_widget(IconLeftWidget(icon=icon, theme_text_color="Custom", text_color=(1, 0, 0, 1) if tipo == 'gasto' else (0, 1, 0, 1)))
                    lista.add_widget(list_item)
                
        except Exception as e:
            logger.error(f"Error al cargar transacciones: {e}")
    
    def sync_data(self):
        """Ejecuta sincronización de datos"""
        self.show_snackbar("Sincronizando...")
        
        def do_sync():
            result = self.sync_engine.sync_all()
            Clock.schedule_once(lambda dt: self.show_snackbar(f"Sync: {result['uploaded']} subidos, {result['downloaded']} bajados"))
            Clock.schedule_once(lambda dt: self.update_balance())
        
        import threading
        threading.Thread(target=do_sync, daemon=True).start()
    
    def show_menu(self):
        """Muestra menú de opciones"""
        self.show_snackbar("Menú - Próximamente")
    
    def add_gasto(self):
        """Agregar nuevo gasto"""
        self.show_snackbar("Completar campos y guardar")
    
    def guardar_gasto(self):
        """Guarda un gasto"""
        try:
            if hasattr(self.root, 'ids'):
                nombre = self.root.ids.gasto_nombre.text
                monto_str = self.root.ids.gasto_monto.text
                recurrente = self.root.ids.gasto_recurrente.active if hasattr(self.root.ids, 'gasto_recurrente') else False
                
                if not nombre or not monto_str:
                    self.show_snackbar("Completa todos los campos")
                    return
                
                monto = float(monto_str.replace(',', '.'))
                
                if self.gastos_service.crear(nombre, monto, recurrente):
                    self.show_snackbar("¡Gasto guardado!")
                    self.root.ids.gasto_nombre.text = ""
                    self.root.ids.gasto_monto.text = ""
                    self.update_balance()
                else:
                    self.show_snackbar("Error al guardar")
        except Exception as e:
            logger.error(f"Error al guardar gasto: {e}")
            self.show_snackbar("Error al guardar gasto")
    
    def add_ingreso(self):
        """Agregar nuevo ingreso"""
        self.show_snackbar("Completar campos y guardar")
    
    def guardar_ingreso(self):
        """Guarda un ingreso"""
        try:
            if hasattr(self.root, 'ids'):
                concepto = self.root.ids.ingreso_concepto.text
                monto_str = self.root.ids.ingreso_monto.text
                
                if not concepto or not monto_str:
                    self.show_snackbar("Completa todos los campos")
                    return
                
                monto = float(monto_str.replace(',', '.'))
                
                if self.ingresos_service.crear(concepto, monto):
                    self.show_snackbar("¡Ingreso guardado!")
                    self.root.ids.ingreso_concepto.text = ""
                    self.root.ids.ingreso_monto.text = ""
                    self.update_balance()
                else:
                    self.show_snackbar("Error al guardar")
        except Exception as e:
            logger.error(f"Error al guardar ingreso: {e}")
            self.show_snackbar("Error al guardar ingreso")


def run_mobile_app():
    """Punto de entrada para ejecutar la app móvil"""
    OrganizadorApp().run()


if __name__ == '__main__':
    run_mobile_app()
