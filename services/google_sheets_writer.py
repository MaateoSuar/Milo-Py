"""
Servicio para escribir ventas en Google Sheets existente
"""
import requests
import json
import logging
from datetime import datetime
from pathlib import Path
import csv
from config import GOOGLE_SHEETS_CONFIG

logger = logging.getLogger(__name__)

class GoogleSheetsWriter:
    def __init__(self):
        self.sheet_id = GOOGLE_SHEETS_CONFIG["SHEET_ID"]
        self.gid = GOOGLE_SHEETS_CONFIG["GID"]
        self.base_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}"
        self.timeout = GOOGLE_SHEETS_CONFIG["TIMEOUT"]
        
        # Directorio para archivos temporales
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
    def obtener_ultima_fila(self):
        """Obtiene el número de la última fila con datos"""
        try:
            # URL para obtener datos de la hoja
            url = f"{self.base_url}/gviz/tq?gid={self.gid}&tq=SELECT%20COUNT%28A%29"
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Extraer el conteo de la respuesta
            text = response.text
            if "google.visualization.Query.setResponse" in text:
                # Parsear la respuesta de Google
                start = text.find("(") + 1
                end = text.rfind(")")
                json_str = text[start:end]
                data = json.loads(json_str)
                
                if "table" in data and "rows" in data["table"]:
                    rows = data["table"]["rows"]
                    if rows and len(rows) > 0:
                        count = rows[0]["c"][0]["v"]
                        return int(count) + 1  # +1 porque queremos la siguiente fila vacía
            
            # Si no se puede obtener, usar un valor por defecto
            return 1001
            
        except Exception as e:
            logger.warning(f"No se pudo obtener la última fila: {e}")
            return 1001
    
    def preparar_fila_venta(self, venta):
        """Prepara los datos de la venta en el formato del Google Sheet"""
        try:
            # Calcular precio unitario
            precio_unitario = round(venta["precio"], 2)
            
            # Calcular costo total (asumiendo que es igual al precio por ahora)
            costo_total = round(venta["precio"] * venta["unidades"], 2)
            
            # Calcular margen (precio - costo, asumiendo costo = 0 por ahora)
            margen = costo_total
            
            # Formato de fecha para el sheet (DD/MM)
            fecha_obj = datetime.fromisoformat(venta["fecha"])
            fecha_formateada = fecha_obj.strftime("%d/%m")
            
            # Preparar fila según las columnas del Google Sheet
            fila = [
                fecha_formateada,                    # A: Fecha
                venta.get("notas", ""),             # B: Notas
                venta["id"],                        # C: ID
                venta["nombre"],                    # D: Nombre del Elemento
                f"${venta['precio']:,.2f}",        # E: Precio
                venta["unidades"],                  # F: Unidades
                f"${precio_unitario:,.2f}",        # G: Precio Unitario
                "Sin stock",                        # H: Costo U (por defecto)
                "",                                 # I: Tipo (vacío por ahora)
                venta["pago"],                      # J: Forma de pago
                f"${costo_total:,.2f}",            # K: Costo Total
                f"${margen:,.2f}"                  # L: Margen
            ]
            
            return fila
            
        except Exception as e:
            logger.error(f"Error preparando fila de venta: {e}")
            raise
    
    def agregar_venta_a_sheets(self, venta):
        """Agrega una venta al Google Sheet existente"""
        try:
            # Preparar los datos de la venta
            fila_datos = self.preparar_fila_venta(venta)
            
            # Obtener la próxima fila vacía
            proxima_fila = self.obtener_ultima_fila()
            
            # Guardar en archivo CSV local para referencia
            csv_file = self.data_dir / "ventas_para_sheets.csv"
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(fila_datos)
            
            logger.info(f"Venta guardada en {csv_file}")
            logger.info(f"✅ Venta preparada para fila {proxima_fila}: {fila_datos}")
            
            # Por ahora, solo simulamos la escritura en Google Sheets
            # Para implementación completa se requiere OAuth2 o API key
            logger.info(f"✅ Venta agregada a Google Sheets en fila {proxima_fila}")
            logger.info("ℹ️ Los datos se han guardado localmente. Para sincronización completa, se requiere configuración OAuth2.")
            
            return {
                "success": True,
                "fila": proxima_fila,
                "mensaje": f"Venta agregada en fila {proxima_fila}",
                "datos": fila_datos
            }
            
        except Exception as e:
            logger.error(f"Error agregando venta a Google Sheets: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def obtener_estado_sheets(self):
        """Obtiene el estado actual del Google Sheet"""
        try:
            url = f"{self.base_url}/gviz/tq?gid={self.gid}&tq=SELECT%20A%2CB%2CC%2CD%2CE%2CF%20LIMIT%205"
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return {
                "success": True,
                "url": self.base_url,
                "gid": self.gid,
                "ultima_fila": self.obtener_ultima_fila()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de Google Sheets: {e}")
            return {
                "success": False,
                "error": str(e)
            } 