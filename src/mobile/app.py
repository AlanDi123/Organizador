"""
Aplicación Móvil - KivyMD
Punto de entrada para la versión Android/iOS
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from threading import Thread

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.navigationdrawer import MDNavigationDrawer, MDNavigationLayout
from kivymd.uix.list import OneLineAvatarListItem, IconLeftWidget
from kivymd.uix.boxlayout import MDBoxLayout

from src.core.services import GastosService, IngresosService, AuthService, PresupuestoService
from src.cloud.sync_engine import SyncEngine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detección de plataforma Android
IS_ANDROID = sys.platform == "android"


class OrganizadorApp(MDApp):
    """Aplicación principal para móviles"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Organizador de Gastos"
        # Verificar si el icono existe antes de asignarlo
        icon_path = 'assets/icon.png'
        if os.path.exists(icon_path):
            self.icon = icon_path

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
        """Construye la aplicación con manejo robusto de errores"""
        try:
            self.theme_cls.primary_palette = "Pink"
            self.theme_cls.accent_palette = "Purple"
            self.theme_cls.theme_style = "Light"

            # Configurar ventana (solo en desktop, Android ignora esto)
            if not IS_ANDROID:
                Window.size = (360, 640)
                Window.minimum_width, Window.minimum_height = 300, 500

            # Cargar KV y obtener root
            root = Builder.load_string(self.get_main_kv())
            self.sm = root.ids.screen_manager
            self.nav_drawer = root.ids.nav_drawer
            self.setup_navigation_drawer()

            return root

        except Exception as e:
            logger.error(f"FATAL BUILD ERROR: {e}")
            logger.error(traceback.format_exc())
            # Mostrar error en pantalla en lugar de crashear
            from kivy.uix.label import Label
            from kivy.uix.scrollview import ScrollView
            from kivy.uix.boxlayout import BoxLayout
            
            error_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
            error_layout.add_widget(Label(
                text=f"[color=ff0000]FATAL ERROR[/color]\n\n{str(e)}\n\n{traceback.format_exc()}",
                markup=True,
                halign='left',
                valign='top',
                size_hint_y=None,
                height=400
            ))
            
            scroll = ScrollView(size_hint=(1, 1))
            scroll.add_widget(error_layout)
            return scroll

    def get_main_kv(self) -> str:
        """Retorna el KV principal embebido"""
        return '''
#:import NoTransition kivy.uix.screenmanager.NoTransition

MDNavigationLayout:
    MDScreenManager:
        id: screen_manager
        transition: NoTransition()

    MDNavigationDrawer:
        id: nav_drawer
    
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
        self.nav_drawer.set_state("close")
        self.nav_drawer.clear_widgets()

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

        # No se agrega al ScreenManager; ya vive dentro del MDNavigationLayout del KV
    
    def on_start(self):
        """Se ejecuta al iniciar la app - TODO en hilo separado para evitar ANR"""
        logger.info("App iniciada")
        # Mover operaciones de red a hilo separado para evitar ANR
        Thread(target=self._init_app_background, daemon=True).start()
    
    def _init_app_background(self):
        """Inicialización en segundo plano (red, auth, sync)"""
        try:
            self.check_auth_status()
        except Exception as e:
            logger.error(f"Error en inicialización background: {e}")
            Clock.schedule_once(lambda dt: self.show_snackbar(f"Error inicio: {str(e)}"), 0)

    def check_auth_status(self):
        """Verifica estado de autenticación (ejecutar en hilo separado)"""
        try:
            if self.auth_service.esta_autenticado():
                self.user_logged = True
                Clock.schedule_once(lambda dt: self.go_to_screen('home'), 0)
                Clock.schedule_once(lambda dt: self.update_balance(), 0)
            else:
                Clock.schedule_once(lambda dt: self.go_to_screen('login'), 0)
        except Exception as e:
            logger.error(f"Error en check_auth_status: {e}")
            Clock.schedule_once(lambda dt: self.go_to_screen('login'), 0)
    
    def login(self):
        """Intenta iniciar sesión - auth en hilo separado"""
        login_ids = self.sm.get_screen('login').ids
        email = login_ids.email_field.text.strip()
        password = login_ids.password_field.text.strip()

        if not email or not password:
            self.show_snackbar("Completa email y contraseña")
            return

        # Ejecutar auth en hilo separado
        def do_login():
            try:
                if self.auth_service.login(email, password):
                    self.user_logged = True
                    Clock.schedule_once(lambda dt: self.show_snackbar("¡Bienvenido!"), 0)
                    Clock.schedule_once(lambda dt: self.go_to_screen('home'), 0)
                    Clock.schedule_once(lambda dt: self.update_balance(), 0)
                else:
                    Clock.schedule_once(lambda dt: self.show_snackbar("Error de autenticación"), 0)
            except Exception as e:
                logger.error(f"Error en login: {e}")
                Clock.schedule_once(lambda dt: self.show_snackbar(f"Error: {str(e)}"), 0)

        Thread(target=do_login, daemon=True).start()
    
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

            # Actualizar UI - acceder a través de la pantalla home
            try:
                home_ids = self.sm.get_screen('home').ids
                home_ids.balance_label.text = f"$ {self.current_balance:,.2f}"
                
                # Actualizar último sync
                sync_status = self.sync_engine.get_sync_status()
                if sync_status.get('last_sync'):
                    last_sync = sync_status['last_sync']
                    home_ids.last_sync_label.text = f"Última sync: {last_sync}"
            except KeyError:
                pass  # La pantalla home no está disponible aún

            # Cargar transacciones recientes
            self.load_recent_transactions()

        except Exception as e:
            logger.error(f"Error al actualizar balance: {e}")
    
    def load_recent_transactions(self):
        """Carga transacciones recientes en la lista"""
        try:
            # Limpiar lista - acceder a través de la pantalla home
            try:
                home_ids = self.sm.get_screen('home').ids
                lista = home_ids.recent_transactions
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
            except KeyError:
                pass  # La pantalla home no está disponible aún

        except Exception as e:
            logger.error(f"Error al cargar transacciones: {e}")
    
    def sync_data(self):
        """Ejecuta sincronización de datos"""
        self.show_snackbar("Sincronizando...")

        def do_sync():
            result = self.sync_engine.sync_all() or {}
            Clock.schedule_once(
                lambda dt: self.show_snackbar(
                    f"Sync: {result.get('uploaded', 0)} subidos, {result.get('downloaded', 0)} bajados"
                )
            )
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
            try:
                gastos_ids = self.sm.get_screen('gastos').ids
                nombre = gastos_ids.gasto_nombre.text
                monto_str = gastos_ids.gasto_monto.text
                recurrente = gastos_ids.gasto_recurrente.active if hasattr(gastos_ids, 'gasto_recurrente') else False
            except KeyError:
                self.show_snackbar("Error: pantalla de gastos no disponible")
                return

            if not nombre or not monto_str:
                self.show_snackbar("Completa todos los campos")
                return

            monto = float(monto_str.replace(',', '.'))

            if self.gastos_service.crear(nombre, monto, recurrente):
                self.show_snackbar("¡Gasto guardado!")
                gastos_ids.gasto_nombre.text = ""
                gastos_ids.gasto_monto.text = ""
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
            try:
                ingresos_ids = self.sm.get_screen('ingresos').ids
                concepto = ingresos_ids.ingreso_concepto.text
                monto_str = ingresos_ids.ingreso_monto.text
            except KeyError:
                self.show_snackbar("Error: pantalla de ingresos no disponible")
                return

            if not concepto or not monto_str:
                self.show_snackbar("Completa todos los campos")
                return

            monto = float(monto_str.replace(',', '.'))

            if self.ingresos_service.crear(concepto, monto):
                self.show_snackbar("¡Ingreso guardado!")
                ingresos_ids.ingreso_concepto.text = ""
                ingresos_ids.ingreso_monto.text = ""
                self.update_balance()
            else:
                self.show_snackbar("Error al guardar")
        except Exception as e:
            logger.error(f"Error al guardar ingreso: {e}")
            self.show_snackbar("Error al guardar ingreso")

    def on_stop(self):
        """Limpieza al cerrar la app"""
        logger.info("App cerrándose")
        # Cancelar sync periódico si existe
        if getattr(self, "_sync_event", None):
            self._sync_event.cancel()


def run_mobile_app():
    """Punto de entrada para ejecutar la app móvil"""
    OrganizadorApp().run()


if __name__ == '__main__':
    run_mobile_app()
