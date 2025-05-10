# exportador.py
import csv
import json
import os
import logging
import threading
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='exportador.log'
)
logger = logging.getLogger('exportador')

class Exportador:
    """Clase para exportar datos de la aplicación en diferentes formatos"""
    
    @staticmethod
    def exportar_csv(datos, ruta_archivo, cabeceras=None):
        """
        Exporta datos a un archivo CSV.
        
        Args:
            datos (list): Lista de filas a exportar
            ruta_archivo (str): Ruta completa del archivo destino
            cabeceras (list, optional): Lista de cabeceras para el CSV
            
        Returns:
            bool: True si la exportación fue exitosa, False en caso contrario
        """
        try:
            # Asegurar que el directorio exista
            os.makedirs(os.path.dirname(os.path.abspath(ruta_archivo)), exist_ok=True)
            
            # Exportar datos
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo:
                escritor = csv.writer(archivo)
                
                # Escribir cabeceras si se proporcionaron
                if cabeceras:
                    escritor.writerow(cabeceras)
                
                # Escribir datos
                for fila in datos:
                    escritor.writerow(fila)
            
            logger.info(f"Datos exportados exitosamente a {ruta_archivo}")
            return True
        except Exception as e:
            logger.error(f"Error al exportar a CSV: {e}")
            return False
    
    @staticmethod
    def exportar_json(datos, ruta_archivo):
        """
        Exporta datos a un archivo JSON.
        
        Args:
            datos (dict/list): Datos a exportar en formato JSON
            ruta_archivo (str): Ruta completa del archivo destino
            
        Returns:
            bool: True si la exportación fue exitosa, False en caso contrario
        """
        try:
            # Asegurar que el directorio exista
            os.makedirs(os.path.dirname(os.path.abspath(ruta_archivo)), exist_ok=True)
            
            # Exportar datos
            with open(ruta_archivo, 'w', encoding='utf-8') as archivo:
                json.dump(datos, archivo, indent=4, ensure_ascii=False)
            
            logger.info(f"Datos exportados exitosamente a {ruta_archivo}")
            return True
        except Exception as e:
            logger.error(f"Error al exportar a JSON: {e}")
            return False
    
    @staticmethod
    def exportar_en_hilo(formato, datos, ruta_archivo, cabeceras=None, callback=None):
        """
        Exporta datos en un hilo separado para no bloquear la UI.
        
        Args:
            formato (str): 'csv' o 'json'
            datos (list/dict): Datos a exportar
            ruta_archivo (str): Ruta del archivo
            cabeceras (list, optional): Cabeceras para CSV
            callback (function, optional): Función a llamar cuando termine
            
        Returns:
            thread: Objeto de hilo iniciado
        """
        def _exportar():
            resultado = False
            try:
                if formato.lower() == 'csv':
                    resultado = Exportador.exportar_csv(datos, ruta_archivo, cabeceras)
                elif formato.lower() == 'json':
                    resultado = Exportador.exportar_json(datos, ruta_archivo)
                else:
                    logger.error(f"Formato de exportación no reconocido: {formato}")
                    resultado = False
            except Exception as e:
                logger.error(f"Error durante exportación: {e}")
                resultado = False
            finally:
                # Llamar al callback si se proporcionó
                if callback:
                    callback(resultado)
        
        # Crear e iniciar el hilo
        hilo = threading.Thread(target=_exportar, daemon=True)
        hilo.start()
        return hilo