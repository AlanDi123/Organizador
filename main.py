"""
Main entry point for Buildozer (Android APK)
Diagnóstico: captura errores de import antes de que Kivy arranque
"""
import os
os.environ['KIVY_NO_CONSOLELOG'] = '0'

import sys
import traceback

# Capturar CUALQUIER error antes de que Kivy arranque
_boot_error = None

try:
    from src.mobile.app import run_mobile_app
except Exception as e:
    _boot_error = traceback.format_exc()

if __name__ == '__main__':
    if _boot_error:
        # Mostrar el error en pantalla con Kivy puro (sin KivyMD)
        from kivy.app import App
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.label import Label

        class ErrorApp(App):
            def build(self):
                sv = ScrollView()
                lbl = Label(
                    text=f"[b]ERROR DE IMPORTACION:[/b]\n\n{_boot_error}",
                    markup=True,
                    size_hint_y=None,
                    font_size='12sp',
                    halign='left',
                    valign='top',
                    padding=(10, 10),
                )
                lbl.bind(texture_size=lbl.setter('size'))
                sv.add_widget(lbl)
                return sv

        ErrorApp().run()
    else:
        run_mobile_app()
