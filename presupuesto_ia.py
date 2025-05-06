# model/presupuesto_ia.py
import numpy as np
from datetime import datetime, timedelta
import json
import os
from model.data_manager import cargar_datos
from model.ia_module import modulo_ia

class PresupuestoInteligente:
    def __init__(self):
        """Inicializa el sistema de presupuesto inteligente"""
        self.ruta_presupuesto = "presupuesto_ia.json"
        self.presupuesto_actual = self.cargar_presupuesto_actual()
        self.historico_gastos = []
        self.historico_ingresos = []
        self.cargar_datos_historicos()
    
    def cargar_datos_historicos(self):
        """Carga datos históricos para análisis y generación de presupuesto"""
        try:
            # Cargar datos crudos
            gastos_raw = cargar_datos('gastos')
            ingresos_raw = cargar_datos('ingresos')
            
            # Procesar datos con el módulo de IA
            self.historico_gastos = modulo_ia.procesar_gastos(gastos_raw)
            self.historico_ingresos = modulo_ia.procesar_ingresos(ingresos_raw)
            
            print(f"Datos históricos cargados para presupuesto: {len(self.historico_gastos)} gastos, {len(self.historico_ingresos)} ingresos")
        except Exception as e:
            print(f"Error al cargar datos históricos para presupuesto: {e}")
            self.historico_gastos = []
            self.historico_ingresos = []
    
    def cargar_presupuesto_actual(self):
        """Carga el presupuesto existente o crea uno nuevo"""
        try:
            if os.path.exists(self.ruta_presupuesto):
                with open(self.ruta_presupuesto, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error al cargar presupuesto existente: {e}")
            return {}
    
    def guardar_presupuesto(self, presupuesto):
        """Guarda el presupuesto en un archivo JSON"""
        try:
            with open(self.ruta_presupuesto, 'w', encoding='utf-8') as f:
                json.dump(presupuesto, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar presupuesto: {e}")
            return False
    
    def analizar_gastos_historicos(self):
        """Analiza los patrones de gasto históricos para generar recomendaciones"""
        categorias = {}
        
        # Agrupar gastos por categoría
        for gasto in self.historico_gastos:
            categoria = gasto.get('categoria', 'otros')
            if categoria not in categorias:
                categorias[categoria] = []
            categorias[categoria].append(gasto['monto'])
        
        # Calcular estadísticas por categoría
        estadisticas = {}
        for categoria, montos in categorias.items():
            if len(montos) > 0:
                estadisticas[categoria] = {
                    'promedio': sum(montos) / len(montos),
                    'maximo': max(montos),
                    'minimo': min(montos),
                    'total': sum(montos),
                    'cantidad': len(montos)
                }
        
        return estadisticas
    
    def predecir_ingresos_futuros(self):
        """Predice ingresos futuros basado en patrones históricos"""
        if not self.historico_ingresos:
            return 0
            
        # Método simple: promedio de los últimos 3 meses
        # Agrupar por mes
        ingresos_por_mes = {}
        
        for ingreso in self.historico_ingresos:
            try:
                fecha = datetime.strptime(ingreso['fecha'], "%Y-%m-%d")
                clave_mes = f"{fecha.year}-{fecha.month:02d}"
                
                if clave_mes not in ingresos_por_mes:
                    ingresos_por_mes[clave_mes] = 0
                
                ingresos_por_mes[clave_mes] += ingreso['monto']
            except:
                continue
        
        # Ordenar por fecha
        meses_ordenados = sorted(ingresos_por_mes.keys())
        
        # Obtener los últimos 3 meses (o todos si hay menos)
        ultimos_tres = meses_ordenados[-3:] if len(meses_ordenados) >= 3 else meses_ordenados
        
        # Calcular promedio
        if ultimos_tres:
            total = sum(ingresos_por_mes[mes] for mes in ultimos_tres)
            return total / len(ultimos_tres)
        
        return 0
    
    def generar_presupuesto_sugerido(self):
        """Genera un presupuesto sugerido basado en análisis histórico y metas"""
        # Obtener estadísticas de gastos
        estadisticas = self.analizar_gastos_historicos()
        
        # Predecir ingresos
        ingresos_esperados = self.predecir_ingresos_futuros()
        
        # Asignar presupuesto por categoría
        presupuesto = {}
        
        # Si tenemos información histórica
        if estadisticas and ingresos_esperados > 0:
            # Calcular porcentaje de gasto deseable para cada categoría
            # según análisis y mejores prácticas financieras
            porcentajes_ideales = {
                'alimentación': 0.25,  # 25% para alimentación
                'vivienda': 0.30,      # 30% para vivienda
                'transporte': 0.15,    # 15% para transporte
                'servicios': 0.10,     # 10% para servicios
                'ocio': 0.05,          # 5% para ocio
                'salud': 0.05,         # 5% para salud
                'educación': 0.05,     # 5% para educación
                'ahorro': 0.10,        # 10% para ahorro
                'otros': 0.05          # 5% para otros gastos
            }
            
            # Ajustar según gasto histórico y calcular presupuesto sugerido
            for categoria, datos in estadisticas.items():
                # Si la categoría no está en las ideales, asignarla a 'otros'
                cat = categoria if categoria in porcentajes_ideales else 'otros'
                
                # Calcular presupuesto base según el porcentaje ideal
                presupuesto_base = ingresos_esperados * porcentajes_ideales.get(cat, 0.05)
                
                # Ajustar según el gasto histórico
                presupuesto_ajustado = (presupuesto_base + datos['promedio']) / 2
                
                # Limitamos el presupuesto sugerido al porcentaje máximo
                presupuesto_maximo = ingresos_esperados * (porcentajes_ideales.get(cat, 0.05) * 1.2)
                presupuesto_sugerido = min(presupuesto_ajustado, presupuesto_maximo)
                
                # Guardar el presupuesto sugerido
                presupuesto[categoria] = {
                    'sugerido': presupuesto_sugerido,
                    'historico_promedio': datos['promedio'],
                    'explicacion': f"Basado en su gasto histórico promedio (${datos['promedio']:.2f}) y las mejores prácticas financieras."
                }
            
            # Asegurar que todas las categorías ideales tengan un presupuesto
            for categoria, porcentaje in porcentajes_ideales.items():
                if categoria not in presupuesto:
                    presupuesto_sugerido = ingresos_esperados * porcentaje
                    presupuesto[categoria] = {
                        'sugerido': presupuesto_sugerido,
                        'historico_promedio': 0,
                        'explicacion': f"Basado en las mejores prácticas financieras: {porcentaje*100:.1f}% de sus ingresos."
                    }
        else:
            # Si no hay suficiente información histórica, usar porcentajes genéricos
            for categoria, porcentaje in {
                'alimentación': 0.25,
                'vivienda': 0.30,
                'transporte': 0.15,
                'servicios': 0.10,
                'otros': 0.10,
                'ahorro': 0.10
            }.items():
                presupuesto[categoria] = {
                    'sugerido': ingresos_esperados * porcentaje,
                    'historico_promedio': 0,
                    'explicacion': f"Asignación estándar recomendada: {porcentaje*100:.1f}% de sus ingresos."
                }
        
        # Guardar presupuesto
        self.guardar_presupuesto(presupuesto)
        
        return presupuesto
    
    def seguimiento_presupuesto(self, gastos_periodo_actual):
        """Analiza el cumplimiento del presupuesto actual"""
        # Si no hay presupuesto actual, generarlo
        if not self.presupuesto_actual:
            self.presupuesto_actual = self.generar_presupuesto_sugerido()
        
        # Agrupar gastos actuales por categoría
        gastos_por_categoria = {}
        for gasto in gastos_periodo_actual:
            categoria = gasto.get('categoria', 'otros')
            if categoria not in gastos_por_categoria:
                gastos_por_categoria[categoria] = 0
            gastos_por_categoria[categoria] += gasto['monto']
        
        # Comparar con presupuesto
        resultados = {}
        for categoria, presupuesto in self.presupuesto_actual.items():
            gasto_actual = gastos_por_categoria.get(categoria, 0)
            presupuesto_valor = presupuesto.get('sugerido', 0)
            
            if presupuesto_valor > 0:
                porcentaje_utilizado = (gasto_actual / presupuesto_valor) * 100
                
                # Determinar estado
                if porcentaje_utilizado <= 80:
                    estado = "bueno"
                elif porcentaje_utilizado <= 100:
                    estado = "alerta"
                else:
                    estado = "excedido"
                
                resultados[categoria] = {
                    'presupuesto': presupuesto_valor,
                    'gasto_actual': gasto_actual,
                    'porcentaje_utilizado': porcentaje_utilizado,
                    'estado': estado,
                    'restante': presupuesto_valor - gasto_actual
                }
        
        return resultados