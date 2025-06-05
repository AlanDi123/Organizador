from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from gastos import calcular_total_gastos
from ingresos import calcular_total_ingresos
from data_manager import guardar_gasto, guardar_ingreso

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)

        self.total_label = Label(text=self._get_totals())
        self.add_widget(self.total_label)

        gasto_box = BoxLayout(size_hint_y=None, height='40dp', spacing=5)
        self.gasto_nombre = TextInput(hint_text='Nombre del gasto')
        self.gasto_monto = TextInput(hint_text='Monto', input_filter='float')
        gasto_btn = Button(text='Agregar Gasto')
        gasto_btn.bind(on_press=self.agregar_gasto)
        gasto_box.add_widget(self.gasto_nombre)
        gasto_box.add_widget(self.gasto_monto)
        gasto_box.add_widget(gasto_btn)
        self.add_widget(gasto_box)

        ingreso_box = BoxLayout(size_hint_y=None, height='40dp', spacing=5)
        self.ingreso_concepto = TextInput(hint_text='Concepto de ingreso')
        self.ingreso_monto = TextInput(hint_text='Monto', input_filter='float')
        ingreso_btn = Button(text='Agregar Ingreso')
        ingreso_btn.bind(on_press=self.agregar_ingreso)
        ingreso_box.add_widget(self.ingreso_concepto)
        ingreso_box.add_widget(self.ingreso_monto)
        ingreso_box.add_widget(ingreso_btn)
        self.add_widget(ingreso_box)

    def _get_totals(self):
        total_gastos = calcular_total_gastos()
        total_ingresos = calcular_total_ingresos()
        return f'Total gastos: {total_gastos:.2f} | Total ingresos: {total_ingresos:.2f}'

    def agregar_gasto(self, instance):
        nombre = self.gasto_nombre.text.strip()
        monto = self.gasto_monto.text.strip()
        if nombre and monto:
            if guardar_gasto(nombre, monto, False):
                self.gasto_nombre.text = ''
                self.gasto_monto.text = ''
                self.total_label.text = self._get_totals()

    def agregar_ingreso(self, instance):
        concepto = self.ingreso_concepto.text.strip()
        monto = self.ingreso_monto.text.strip()
        if concepto and monto:
            if guardar_ingreso(concepto, monto):
                self.ingreso_concepto.text = ''
                self.ingreso_monto.text = ''
                self.total_label.text = self._get_totals()

class OrganizadorApp(App):
    def build(self):
        return MainLayout()

if __name__ == '__main__':
    OrganizadorApp().run()
