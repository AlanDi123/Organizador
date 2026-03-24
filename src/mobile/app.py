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
from kivy.logger import Logger

from src.core.services import GastosService, IngresosService, AuthService, PresupuestoService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detección de plataforma Android
IS_ANDROID = sys.platform == "android"

# Modo diagnóstico: python -c "import os; os.environ['DIAGNOSTIC_MODE']='1'"
DIAGNOSTIC_MODE = os.environ.get('DIAGNOSTIC_MODE', '0') == '1'


class OrganizadorApp(MDApp):
    """Aplicación principal para móviles"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Organizador de Gastos"
        # Verificar si el icono existe antes de asignarlo
        # En Android, los recursos se empaquetan, verificar existencia real
        icon_paths = ['assets/icon.png', 'icon.png', '../assets/icon.png']
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.icon = icon_path
                Logger.info(f"Icono encontrado: {icon_path}")
                break
        else:
            Logger.warning("Icono no encontrado, usando icono por defecto de Kivy")

        # Servicios - inicializar como None, se crean en build()
        self.gastos_service = None
        self.ingresos_service = None
        self.auth_service = None
        self.presupuesto_service = None
        self.sync_engine = None  # Lazy init después del build

        # Estado
        self.user_logged = False
        self.current_balance = 0.0

    def build(self):
        """Construye la aplicación con manejo robusto de errores"""
        Logger.info("=" * 50)
        Logger.info("INICIANDO ORGANIZADOR FINANZAS")
        Logger.info(f"DIAGNOSTIC_MODE: {DIAGNOSTIC_MODE}")
        Logger.info("=" * 50)

        # MODO DIAGNÓSTICO: Retorna UI minimalista para testear KivyMD
        if DIAGNOSTIC_MODE:
            Logger.warning("=== MODO DIAGNÓSTICO ACTIVADO ===")
            from kivymd.uix.label import MDLabel
            from kivymd.uix.boxlayout import MDBoxLayout
            layout = MDBoxLayout(orientation='vertical')
            layout.add_widget(MDLabel(
                text="✅ KivyMD Funciona!\n\nSi ves esto, el problema está en tu KV o servicios.",
                halign="center",
                valign="center",
                font_style="H5"
            ))
            layout.add_widget(MDLabel(
                text=f"Platform: {sys.platform}\nAndroid: {IS_ANDROID}",
                halign="center",
                theme_text_color="Secondary"
            ))
            return layout

        try:
            # 1. Configurar tema (puede fallar si kivymd no está disponible)
            Logger.info("Configurando tema MD...")
            self.theme_cls.primary_palette = "Pink"
            self.theme_cls.accent_palette = "Purple"
            self.theme_cls.theme_style = "Light"
            Logger.info("Tema configurado")

            # 2. Configurar ventana (solo en desktop, Android ignora esto)
            if not IS_ANDROID:
                Window.size = (360, 640)
                Window.minimum_width, Window.minimum_height = 300, 500
            Logger.info("Ventana configurada")

            # 3. Cargar KV PRIMERO (antes de servicios, para detectar errores de UI)
            Logger.info("Cargando archivo KV...")
            kv_string = self.get_main_kv()
            Logger.debug(f"KV string length: {len(kv_string)}")
            root = Builder.load_string(kv_string)
            Logger.info("KV cargado exitosamente")

            # 4. Verificar IDs requeridos
            Logger.info("Verificando widgets requeridos...")
            if not hasattr(root, 'ids'):
                raise AttributeError("Root widget no tiene 'ids' attribute")
            if 'screen_manager' not in root.ids:
                raise KeyError("Falta 'screen_manager' en root.ids")
            if 'nav_drawer' not in root.ids:
                raise KeyError("Falta 'nav_drawer' en root.ids")
            Logger.info("Widgets verificados")

            # 5. Configurar referencias UI
            self.sm = root.ids.screen_manager
            self.nav_drawer = root.ids.nav_drawer
            self.setup_navigation_drawer()
            Logger.info("UI configurada")

            # 6. Inicializar servicios (puede fallar en Android sin DB)
            Logger.info("Inicializando servicios...")
            try:
                self.gastos_service = GastosService()
                self.ingresos_service = IngresosService()
                self.auth_service = AuthService()
                self.presupuesto_service = PresupuestoService()
                Logger.info("Servicios inicializados")
            except Exception as svc_error:
                Logger.warning(f"Servicios fallaron (continuar sin ellos): {svc_error}")
                self.gastos_service = None
                self.ingresos_service = None
                self.auth_service = None
                self.presupuesto_service = None

            Logger.info("=== APP INICIADA EXITOSAMENTE ===")

            # 7. Inicializar Firebase/Sync en hilo separado (después del build)
            Clock.schedule_once(self._lazy_init_cloud, 0.1)

            return root

        except Exception as e:
            Logger.error("=" * 50)
            Logger.error("CRASH DURANTE BUILD")
            Logger.error(f"Error: {e}")
            Logger.error(f"Traceback: {traceback.format_exc()}")
            Logger.error("=" * 50)

            # Mostrar error en pantalla en lugar de crashear
            from kivy.uix.label import Label
            from kivy.uix.scrollview import ScrollView
            from kivy.uix.boxlayout import BoxLayout

            error_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
            error_label = Label(
                text=f"[color=ff0000][b]FATAL ERROR[/b][/color]\n\n[color=ffff00]{str(e)}[/color]\n\n{traceback.format_exc()}",
                markup=True,
                halign='left',
                valign='top',
                size_hint_y=None,
                height=800,
                padding_x=dp(10),
                font_size=dp(12)
            )
            error_label.bind(texture_size=error_label.setter(size))
            error_layout.add_widget(error_label)

            scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
            scroll.add_widget(error_layout)
            
            Logger.error("Mostrando pantalla de error en lugar de crash")
            return scroll

    def _lazy_init_cloud(self, dt):
        """Inicializa Firebase y Sync en hilo separado para evitar ANR"""
        def init_cloud():
            try:
                Logger.info("Inicializando Firebase/Sync...")
                from src.cloud.sync_engine import SyncEngine
                self.sync_engine = SyncEngine()
                Logger.info("Firebase/Sync inicializados")
            except Exception as e:
                Logger.error(f"Error inicializando cloud: {e}")
                Logger.error(traceback.format_exc())
                # No mostrar snackbar aquí, puede que la UI no esté lista

        Thread(target=init_cloud, daemon=True).start()

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
        """Configura el navigation drawer con estructura correcta de KivyMD 1.x"""
        self.nav_drawer.set_state("close")
        self.nav_drawer.clear_widgets()

        # Fix 14: Importar componentes correctos de KivyMD 1.x
        from kivymd.uix.navigationdrawer import (
            MDNavigationDrawerMenu,
            MDNavigationDrawerHeader,
            MDNavigationDrawerItem,
            MDNavigationDrawerDivider,
        )

        # Menú principal (wrapper requerido por KivyMD 1.x)
        menu = MDNavigationDrawerMenu()

        # Header
        menu.add_widget(MDNavigationDrawerHeader(
            title="Organizador",
            title_color=self.theme_cls.primary_color,
            text="Finanzas Personales",
        ))

        menu.add_widget(MDNavigationDrawerDivider())

        # Items del menú
        items = [
            ("home", "home", "Inicio"),
            ("gastos", "cart", "Gastos"),
            ("ingresos", "cash", "Ingresos"),
            ("dashboard", "chart-pie", "Dashboard"),
        ]

        for screen_name, icon, text in items:
            item = MDNavigationDrawerItem(
                icon=icon,
                text=text,
                on_release=lambda x, s=screen_name: self.go_to_screen(s),
            )
            menu.add_widget(item)

        menu.add_widget(MDNavigationDrawerDivider())

        # Logout
        logout_item = MDNavigationDrawerItem(
            icon="logout",
            text="Cerrar Sesión",
            on_release=lambda x: self.logout(),
        )
        menu.add_widget(logout_item)

        self.nav_drawer.add_widget(menu)
    
    def on_start(self):
        """Se ejecuta al iniciar la app - TODO en hilo separado para evitar ANR"""
        logger.info("App iniciada")
        # Mover operaciones de red a hilo separado para evitar ANR
        Thread(target=self._init_app_background, daemon=True).start()
        # Fix 6: Auto-sync periódico cada 30 segundos
        Clock.schedule_interval(self._auto_sync_tick, 30)

    def _auto_sync_tick(self, dt):
        """Tick periódico de sync (cada 30s)"""
        if self.sync_engine and self.auth_service and self.auth_service.esta_autenticado():
            Thread(target=self.sync_engine.sync_all, daemon=True).start()
    
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
            if not self.gastos_service or not self.ingresos_service:
                logger.warning("Servicios no inicializados aún")
                return

            total_gastos = self.gastos_service.calcular_total()
            total_ingresos = self.ingresos_service.calcular_total()
            self.current_balance = total_ingresos - total_gastos

            # Fix 12: Guard - la pantalla home puede no existir aún
            try:
                home_screen = self.sm.get_screen('home')
                if hasattr(home_screen, 'ids') and 'balance_label' in home_screen.ids:
                    home_screen.ids.balance_label.text = f"$ {self.current_balance:,.2f}"
                    if self.sync_engine:
                        sync_status = self.sync_engine.get_sync_status()
                        if sync_status.get('last_sync'):
                            home_screen.ids.last_sync_label.text = f"Sync: {sync_status['last_sync']}"
            except Exception:
                pass  # Pantalla aún no inicializada

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
        if not self.sync_engine:
            self.show_snackbar("Sincronización no disponible aún")
            return

        self.show_snackbar("Sincronizando...")

        def do_sync():
            try:
                result = self.sync_engine.sync_all() or {}
                Clock.schedule_once(
                    lambda dt: self.show_snackbar(
                        f"Sync: {result.get('uploaded', 0)} subidos, {result.get('downloaded', 0)} bajados"
                    )
                )
                Clock.schedule_once(lambda dt: self.update_balance())
            except Exception as e:
                logger.error(f"Error en sync: {e}")
                Clock.schedule_once(
                    lambda dt: self.show_snackbar(f"Error sync: {str(e)}")
                )

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
