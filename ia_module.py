# model/ia_module.py
import numpy as np
from datetime import datetime, timedelta
import os
import json
import sqlite3
from model.data_manager import cargar_datos

class ModuloIA:
    """Clase principal para las funcionalidades de IA del organizador financiero"""
    
    # Modificar el constructor de ModuloIA
    def __init__(self):
        """Inicializa el módulo de IA"""
        # Cargar configuración
        self.config = self.cargar_configuracion()
        
        # Cargar categorías desde la configuración
        self.categorias_gasto = self.config.get('categorias_gasto', {
            # Diccionario de respaldo en caso de error
            'alimentación': ['supermercado', 'verdulería', 'carnicería', 'almacén', 'restaurant', 'comida', 'delivery'],
            'transporte': ['combustible', 'nafta', 'gasolina', 'sube', 'taxi', 'uber', 'colectivo', 'subte', 'peaje'],
            'servicios': ['luz', 'gas', 'agua', 'internet', 'wifi', 'teléfono', 'celular', 'electricidad'],
            'ocio': ['cine', 'teatro', 'concierto', 'salida', 'bar', 'netflix', 'spotify', 'juego', 'libro'],
            'otros': []
        })
        
        # Cargar historial para entrenar el módulo
        self.cargar_datos_historicos()

    
    def cargar_datos_historicos(self):
        """Carga datos históricos para análisis y aprendizaje"""
        try:
            self.gastos_historicos = cargar_datos('gastos')
            self.ingresos_historicos = cargar_datos('ingresos')
            print(f"Datos históricos cargados: {len(self.gastos_historicos)} gastos, {len(self.ingresos_historicos)} ingresos")
        except Exception as e:
            print(f"Error al cargar datos históricos: {e}")
            self.gastos_historicos = []
            self.ingresos_historicos = []
    
    # Añadir este método a ModuloIA
    def cargar_configuracion(self):
        """Carga la configuración de IA desde el archivo JSON"""
        ruta_config = "config/ia_config.json"
        configuracion_default = {
            "categorias_gasto": {
                # ... (configuración por defecto)
            },
            "anomalias": {
                "umbral_z": 2.0,
                "min_gastos_para_deteccion": 5
            },
            "recomendaciones": {
                "umbral_ahorro_bajo": 10,
                "umbral_ahorro_optimo": 20,
                "umbral_concentracion_categoria": 40,
                "umbral_gastos_recurrentes": 60
            }
        }
        
        try:
            # Verificar si existe el directorio config
            if not os.path.exists("config"):
                os.makedirs("config")
            
            # Verificar si existe el archivo de configuración
            if os.path.exists(ruta_config):
                with open(ruta_config, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Crear el archivo con configuración por defecto
                with open(ruta_config, 'w', encoding='utf-8') as f:
                    json.dump(configuracion_default, f, indent=4, ensure_ascii=False)
                return configuracion_default
        except Exception as e:
            print(f"Error al cargar configuración de IA: {e}")
            return configuracion_default
    
    def categorizar_gasto(self, nombre_gasto):
        """
        Categoriza automáticamente un gasto basado en su nombre utilizando palabras clave.
        
        Args:
            nombre_gasto (str): Nombre o descripción del gasto
            
        Returns:
            str: Categoría asignada
        """
        if not nombre_gasto:
            return 'otros'
            
        nombre_lower = nombre_gasto.lower()
        
        # Buscar coincidencias con palabras clave
        for categoria, palabras_clave in self.categorias_gasto.items():
            for palabra in palabras_clave:
                if palabra in nombre_lower:
                    return categoria
        
        # Si no hay coincidencias, devolver 'otros'
        return 'otros'
    
    def procesar_gastos(self, gastos_raw):
        """
        Procesa datos crudos de gastos y añade metadatos como categorías.
        
        Args:
            gastos_raw (list): Lista de tuplas de gastos desde la base de datos
            
        Returns:
            list: Lista de diccionarios de gastos con metadatos adicionales
        """
        gastos_procesados = []
        
        for gasto in gastos_raw:
            # Verificar que sea un gasto válido y no un registro de historial
            if gasto[2] > 0:  # El monto debe ser mayor que cero
                es_historial = False
                if len(gasto) > 5:  # Verificar si tiene el campo es_historial
                    es_historial = bool(gasto[5])
                
                if not es_historial:
                    # Crear diccionario con información del gasto
                    gasto_dict = {
                        'id': gasto[0],
                        'nombre': gasto[1],
                        'monto': gasto[2],
                        'recurrente': bool(gasto[3]) if gasto[3] is not None else False,
                        'fecha': gasto[4] if len(gasto) > 4 and gasto[4] else datetime.now().strftime("%Y-%m-%d"),
                        'categoria': self.categorizar_gasto(gasto[1])
                    }
                    gastos_procesados.append(gasto_dict)
        
        return gastos_procesados
    
    def procesar_ingresos(self, ingresos_raw):
        """
        Procesa datos crudos de ingresos.
        
        Args:
            ingresos_raw (list): Lista de tuplas de ingresos desde la base de datos
            
        Returns:
            list: Lista de diccionarios de ingresos procesados
        """
        ingresos_procesados = []
        
        for ingreso in ingresos_raw:
            # Verificar que sea un ingreso válido y no un registro de historial
            if ingreso[2] > 0:  # El monto debe ser mayor que cero
                es_historial = False
                if len(ingreso) > 4:  # Verificar si tiene el campo es_historial
                    es_historial = bool(ingreso[4])
                
                if not es_historial:
                    # Crear diccionario con información del ingreso
                    ingreso_dict = {
                        'id': ingreso[0],
                        'concepto': ingreso[1],
                        'monto': ingreso[2],
                        'fecha': ingreso[3] if len(ingreso) > 3 and ingreso[3] else datetime.now().strftime("%Y-%m-%d")
                    }
                    ingresos_procesados.append(ingreso_dict)
        
        return ingresos_procesados
    
    def obtener_estadisticas_por_categoria(self, gastos_procesados):
        """
        Calcula estadísticas de gastos agrupados por categoría.
        
        Args:
            gastos_procesados (list): Lista de diccionarios de gastos procesados
            
        Returns:
            dict: Diccionario con estadísticas por categoría
        """
        if not gastos_procesados:
            return {}
            
        # Agrupar por categoría
        categorias = {}
        for gasto in gastos_procesados:
            categoria = gasto['categoria']
            if categoria not in categorias:
                categorias[categoria] = []
            categorias[categoria].append(gasto['monto'])
        
        # Calcular estadísticas
        estadisticas = {}
        for categoria, montos in categorias.items():
            if montos:
                estadisticas[categoria] = {
                    'total': sum(montos),
                    'promedio': sum(montos) / len(montos),
                    'minimo': min(montos),
                    'maximo': max(montos),
                    'cantidad': len(montos)
                }
        
        return estadisticas
    
    def calcular_tendencia_mensual(self, items_procesados, tipo='gastos'):
        """
        Calcula la tendencia mensual de gastos o ingresos.
        
        Args:
            items_procesados (list): Lista de diccionarios (gastos o ingresos)
            tipo (str): 'gastos' o 'ingresos'
            
        Returns:
            dict: Diccionario con totales por mes
        """
        tendencia = {}
        
        # Agrupar por mes
        for item in items_procesados:
            try:
                # Obtener fecha
                fecha_str = item.get('fecha', None)
                if not fecha_str:
                    continue
                    
                # Convertir a objeto datetime
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                
                # Clave para agrupar por año-mes
                clave_mes = f"{fecha.year}-{fecha.month:02d}"
                
                if clave_mes not in tendencia:
                    tendencia[clave_mes] = 0
                
                # Sumar el monto
                tendencia[clave_mes] += item['monto']
            except Exception as e:
                print(f"Error al procesar fecha en tendencia mensual: {e}")
                continue
        
        # Ordenar por fecha
        tendencia_ordenada = {k: tendencia[k] for k in sorted(tendencia.keys())}
        
        return tendencia_ordenada
    
    def detectar_gastos_anomalos(self, gastos_procesados, umbral_z=2.0):
        """
        Detecta gastos anómalos utilizando el z-score por categoría.
        
        Args:
            gastos_procesados (list): Lista de diccionarios de gastos
            umbral_z (float): Umbral de z-score para considerar anómalo
            
        Returns:
            list: Lista de gastos anómalos con metadatos adicionales
        """
        anomalias = []
        
        # Verificar que hay suficientes datos
        if len(gastos_procesados) < 5:
            return anomalias
            
        # Agrupar por categoría
        categorias = {}
        for gasto in gastos_procesados:
            categoria = gasto['categoria']
            if categoria not in categorias:
                categorias[categoria] = []
            categorias[categoria].append(gasto)
        
        # Analizar cada categoría
        for categoria, gastos_cat in categorias.items():
            # Necesitamos al menos 3 gastos para estadísticas significativas
            if len(gastos_cat) < 3:
                continue
                
            # Extraer montos
            montos = [g['monto'] for g in gastos_cat]
            
            # Calcular estadísticas
            media = np.mean(montos)
            desv_std = np.std(montos)
            
            if desv_std == 0:  # Evitar división por cero
                continue
                
            # Detectar anomalías
            for gasto in gastos_cat:
                z_score = abs((gasto['monto'] - media) / desv_std)
                
                if z_score > umbral_z:
                    # Es una anomalía
                    anomalia = gasto.copy()
                    anomalia['z_score'] = z_score
                    anomalia['diferencia_porcentual'] = ((gasto['monto'] - media) / media) * 100
                    anomalia['media_categoria'] = media
                    anomalias.append(anomalia)
        
        # Ordenar por z-score (más anómalos primero)
        return sorted(anomalias, key=lambda x: x.get('z_score', 0), reverse=True)
    
    def generar_recomendaciones(self, gastos_procesados, ingresos_procesados):
        """
        Genera recomendaciones financieras personalizadas.
        
        Args:
            gastos_procesados (list): Lista de diccionarios de gastos
            ingresos_procesados (list): Lista de diccionarios de ingresos
            
        Returns:
            list: Lista de recomendaciones
        """
        recomendaciones = []
        
        # Verificar si hay datos suficientes
        if not gastos_procesados and not ingresos_procesados:
            recomendaciones.append({
                'prioridad': 'baja',
                'descripcion': 'Comience a registrar sus transacciones',
                'detalle': 'Para obtener recomendaciones personalizadas, registre sus ingresos y gastos regularmente. Esto permitirá analizar sus patrones financieros y ofrecer consejos específicos.',
                'impacto_estimado': 'Mejora en planificación financiera'
            })
            return recomendaciones
        
        # Calcular totales
        total_gastos = sum(g['monto'] for g in gastos_procesados)
        total_ingresos = sum(i['monto'] for i in ingresos_procesados)
        balance = total_ingresos - total_gastos
        
        # Calcular porcentaje de ahorro
        porcentaje_ahorro = (balance / total_ingresos * 100) if total_ingresos > 0 else 0
        
        # 1. Recomendación basada en el balance
        if balance < 0:
            recomendaciones.append({
                'prioridad': 'alta',
                'descripcion': 'Balance negativo detectado',
                'detalle': f'Sus gastos (${total_gastos:.2f}) superan sus ingresos (${total_ingresos:.2f}). Considere reducir gastos no esenciales o buscar fuentes adicionales de ingreso para evitar endeudamiento.',
                'impacto_estimado': f'Reducir al menos ${abs(balance):.2f} en gastos mensuales'
            })
        elif porcentaje_ahorro < 10 and porcentaje_ahorro >= 0:
            recomendaciones.append({
                'prioridad': 'media',
                'descripcion': 'Aumentar tasa de ahorro',
                'detalle': f'Su tasa de ahorro actual es {porcentaje_ahorro:.1f}%. Se recomienda alcanzar al menos un 10% para crear un fondo de emergencia adecuado.',
                'impacto_estimado': f'Incrementar ahorro en ${(total_ingresos * 0.1) - balance:.2f} mensuales'
            })
        
        # 2. Análisis de categorías de gasto
        if gastos_procesados:
            # Agrupar por categoría
            categorias = {}
            for gasto in gastos_procesados:
                categoria = gasto['categoria']
                if categoria not in categorias:
                    categorias[categoria] = 0
                categorias[categoria] += gasto['monto']
            
            # Identificar categoría con mayor gasto
            if categorias:
                categoria_mayor = max(categorias.items(), key=lambda x: x[1])
                porcentaje_mayor = (categoria_mayor[1] / total_gastos * 100) if total_gastos > 0 else 0
                
                if porcentaje_mayor > 40:
                    recomendaciones.append({
                        'prioridad': 'media',
                        'descripcion': f'Optimizar gastos en {categoria_mayor[0]}',
                        'detalle': f'El {porcentaje_mayor:.1f}% de sus gastos se concentra en {categoria_mayor[0]}. Considere revisar estos gastos para identificar oportunidades de ahorro.',
                        'impacto_estimado': f'Potencial ahorro de ${categoria_mayor[1] * 0.2:.2f} (20%)'
                    })
        
        # 3. Análisis de gastos recurrentes
        gastos_recurrentes = [g for g in gastos_procesados if g.get('recurrente', False)]
        monto_recurrentes = sum(g['monto'] for g in gastos_recurrentes)
        
        if gastos_recurrentes and monto_recurrentes > 0:
            porcentaje_recurrentes = (monto_recurrentes / total_gastos * 100) if total_gastos > 0 else 0
            
            if porcentaje_recurrentes > 60:
                recomendaciones.append({
                    'prioridad': 'media',
                    'descripcion': 'Alta proporción de gastos recurrentes',
                    'detalle': f'El {porcentaje_recurrentes:.1f}% de sus gastos son recurrentes. Revise suscripciones y servicios para identificar aquellos que podría reducir o eliminar.',
                    'impacto_estimado': 'Mayor flexibilidad financiera'
                })
        
        # 4. Recomendación de ahorro
        if porcentaje_ahorro >= 20:
            recomendaciones.append({
                'prioridad': 'baja',
                'descripcion': 'Optimizar inversiones',
                'detalle': f'Su tasa de ahorro es excelente ({porcentaje_ahorro:.1f}%). Considere diversificar sus ahorros en inversiones para protegerlos contra la inflación y generar rendimientos.',
                'impacto_estimado': 'Crecimiento a largo plazo del patrimonio'
            })
        
        # 5. Recomendaciones adicionales si son necesarias
        if len(recomendaciones) < 3:
            recomendaciones.append({
                'prioridad': 'baja',
                'descripcion': 'Seguimiento regular',
                'detalle': 'Mantenga un registro constante de sus ingresos y gastos para identificar nuevas oportunidades de optimización financiera.',
                'impacto_estimado': 'Mejora continua en hábitos financieros'
            })
        
        return recomendaciones

# Crear instancia global para uso en la aplicación
modulo_ia = ModuloIA()