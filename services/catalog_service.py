"""
Servicio robusto para leer el catálogo desde Google Sheets
Usa gspread directamente para mejor manejo de errores y permisos
"""
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from config import GOOGLE_SHEETS_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CatalogService:
    def __init__(self):
        try:
            logger.info("Inicializando CatalogService...")
            self.sheet_id = GOOGLE_SHEETS_CONFIG["SHEET_ID"]
            self.catalog_gid = GOOGLE_SHEETS_CONFIG.get("CATALOG_GID", 0)
            
            # Scope necesario para leer Google Sheets
            self.scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Cargar credenciales desde variables/archivo/config
            raw_env = (
                os.getenv("GOOGLE_CREDENTIALS")
                or os.getenv("GOOGLE_CREDENTIALS_JSON")
                or os.getenv("GOOGLE_SHEETS_CREDENTIALS")
            )

            credentials = None
            if raw_env:
                try:
                    credentials = json.loads(raw_env)
                    logger.info("Credenciales cargadas desde variable de entorno")
                except Exception as e:
                    raise ValueError(f"GOOGLE_*_CREDENTIALS no es JSON válido: {e}")
            else:
                credentials = GOOGLE_SHEETS_CONFIG.get("CREDENTIALS", {})
                if not credentials and os.path.exists("google_credentials.json"):
                    with open("google_credentials.json", "r", encoding="utf-8") as f:
                        credentials = json.load(f)
                    logger.info("Credenciales cargadas desde archivo local")

            if not isinstance(credentials, dict) or not credentials:
                raise ValueError("No se encontraron credenciales válidas para el catálogo")

            # Normalizar private_key si vino con "\\n"
            if isinstance(credentials.get("private_key"), str):
                credentials["private_key"] = credentials["private_key"].replace("\\n", "\n")

            # Inicializar cliente con helper de gspread (usa google-auth)
            self.client = gspread.service_account_from_dict(credentials)
            
            # Abrir la hoja
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            
            # Obtener la hoja del catálogo por GID o nombre
            if self.catalog_gid and str(self.catalog_gid).isdigit() and int(self.catalog_gid) > 0:
                try:
                    gid_int = int(self.catalog_gid)
                    self.worksheet = self.spreadsheet.get_worksheet_by_id(gid_int)
                    if not self.worksheet:
                        raise ValueError(f"No se encontró hoja con GID {gid_int}")
                except Exception as e:
                    logger.warning(f"No se pudo obtener hoja por GID {gid_int}: {e}")
                    # Fallback: usar la primera hoja
                    self.worksheet = self.spreadsheet.sheet1
            else:
                # Usar la primera hoja si no se especifica GID válido
                self.worksheet = self.spreadsheet.sheet1
            
            logger.info(f"Catálogo conectado: {self.worksheet.title}")
            
        except Exception as e:
            error_msg = f"Error al inicializar CatalogService: {str(e)}"
            logger.error(error_msg)
            raise
    
    def buscar_columna_flexible(self, headers, patrones_busqueda):
        """
        Busca una columna de forma flexible usando múltiples patrones
        """
        headers_lower = [h.lower().strip() if h else "" for h in headers]
        
        for patron in patrones_busqueda:
            patron_lower = patron.lower()
            
            # Búsqueda exacta
            for i, header in enumerate(headers_lower):
                if header == patron_lower:
                    logger.info(f"Columna '{patron}' encontrada en posición {i}")
                    return i
            
            # Búsqueda parcial
            for i, header in enumerate(headers_lower):
                if patron_lower in header or header in patron_lower:
                    logger.info(f"Columna '{patron}' encontrada parcialmente en posición {i} (header: '{headers[i]}')")
                    return i
        
        return None
    
    def obtener_catalogo(self):
        """
        Descarga el catálogo desde Google Sheets y devuelve un diccionario con la estructura:
        {
            "ID1": {"nombre": "Nombre Producto 1", "precio": 1000},
            "ID2": {"nombre": "Nombre Producto 2", "precio": 2000},
            ...
        }
        """
        try:
            logger.info("Descargando catálogo desde Google Sheets...")
            
            # Verificar permisos primero
            try:
                test_cell = self.worksheet.acell('A1').value
                logger.info("Permisos de lectura verificados correctamente")
            except gspread.exceptions.APIError as e:
                error_msg = str(e).lower()
                if "permission" in error_msg or "denied" in error_msg:
                    raise RuntimeError(
                        "PERMISSION_DENIED: No tienes permisos para leer esta hoja. "
                        "Verifica que la cuenta de servicio tenga acceso de lectura."
                    )
                else:
                    raise RuntimeError(f"Error del API de Google Sheets: {e}")
            
            # Obtener todos los valores de la hoja
            all_values = self.worksheet.get_all_values()
            
            if not all_values:
                logger.warning("La hoja del catálogo está vacía")
                return {}
            
            # La primera fila son los headers
            headers = all_values[0]
            logger.info(f"Headers encontrados: {headers}")
            
            # Buscar columnas de forma flexible
            patrones_id = ["id", "código", "sku", "codigo", "producto_id"]
            patrones_nombre = ["nombre", "descripción", "descripcion", "producto", "item", "elemento"]
            patrones_precio = ["precio", "valor", "costo", "precio_venta", "venta"]
            
            idx_id = self.buscar_columna_flexible(headers, patrones_id)
            idx_nombre = self.buscar_columna_flexible(headers, patrones_nombre)
            idx_precio = self.buscar_columna_flexible(headers, patrones_precio)
            
            if idx_id is None:
                raise RuntimeError(
                    f"No se encontró columna de ID. Headers disponibles: {headers}. "
                    f"Patrones buscados: {patrones_id}"
                )
            
            if idx_nombre is None:
                logger.warning(
                    f"No se encontró columna de Nombre. Usando 'Producto Desconocido'. "
                    f"Headers disponibles: {headers}. Patrones buscados: {patrones_nombre}"
                )
            
            if idx_precio is None:
                logger.warning(
                    f"No se encontró columna de Precio. Usando 0 como valor por defecto. "
                    f"Headers disponibles: {headers}. Patrones buscados: {patrones_precio}"
                )
            
            # Procesar filas de datos (excluyendo headers)
            catalogo = {}
            rows_processed = 0
            rows_skipped = 0
            
            for row_idx, row in enumerate(all_values[1:], start=2):
                try:
                    # Verificar que la fila tenga suficientes columnas
                    max_col = max(
                        idx_id if idx_id is not None else 0,
                        idx_nombre if idx_nombre is not None else 0,
                        idx_precio if idx_precio is not None else 0
                    )
                    
                    if len(row) <= max_col:
                        logger.debug(f"Fila {row_idx} ignorada: insuficientes columnas")
                        rows_skipped += 1
                        continue
                    
                    # Obtener valores de las columnas
                    id_val = row[idx_id] if idx_id is not None and len(row) > idx_id else ""
                    nombre_val = row[idx_nombre] if idx_nombre is not None and len(row) > idx_nombre else "Producto Desconocido"
                    precio_val = row[idx_precio] if idx_precio is not None and len(row) > idx_precio else "0"
                    
                    # Limpiar y validar valores
                    if id_val:
                        id_clean = str(id_val).strip()
                        nombre_clean = str(nombre_val).strip()
                        
                        # Limpiar el nombre para quitar información de precio
                        # Quitar cualquier patrón de precio que esté en el nombre
                        import re
                        # Quitar "precio sugerido" y patrones de moneda/números
                        nombre_clean = re.sub(r'\bprecio\s*sugerido\b[:\-]?\s*', '', nombre_clean, flags=re.IGNORECASE)
                        # Quitar patrones como "- $250", "-$250", "($250)", "$250", "2500 CLP", etc.
                        nombre_clean = re.sub(r'\s*[-–]\s*\$?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\s*', '', nombre_clean)  # Quitar "- $250" o con miles
                        nombre_clean = re.sub(r'\s*\(\$?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\)\s*', '', nombre_clean)  # Quitar "($250)"
                        nombre_clean = re.sub(r'\s*\$?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\s*$', '', nombre_clean)  # Quitar precio al final
                        nombre_clean = re.sub(r'\s*\$?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\s*', '', nombre_clean)  # Quitar precio en cualquier parte
                        nombre_clean = re.sub(r'\s*Rango\s*de\s*precios\s*\d*\s*', '', nombre_clean, flags=re.IGNORECASE)  # Quitar "Rango de precios 1"
                        nombre_clean = re.sub(r'\s*\d+\s*$', '', nombre_clean)  # Quitar números al final
                        nombre_clean = nombre_clean.strip()
                        
                        # Limpiar y convertir el precio
                        try:
                            # Eliminar símbolos de moneda y espacios
                            precio_limpio = str(precio_val).replace('$', '').replace(' ', '').replace(',', '.').strip()
                            precio_float = float(precio_limpio) if precio_limpio else 0.0
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error convirtiendo precio '{precio_val}' a número: {e}")
                            precio_float = 0.0
                        
                        # Solo agregar si el ID es válido
                        if id_clean and id_clean.lower() not in ['', 'n/a', 'null', 'none']:
                            # Convertir ID a mayúsculas para consistencia
                            id_clean = id_clean.upper()
                            catalogo[id_clean] = {
                                'nombre': nombre_clean,
                                'precio': precio_float
                            }
                            rows_processed += 1
                        else:
                            rows_skipped += 1
                    else:
                        rows_skipped += 1
                        
                except Exception as e:
                    logger.warning(f"Error procesando fila {row_idx}: {e}")
                    rows_skipped += 1
                    continue
            
            logger.info(f"Catálogo procesado: {len(catalogo)} productos de {rows_processed} filas válidas")
            if rows_skipped > 0:
                logger.info(f"Filas ignoradas: {rows_skipped}")
            
            return catalogo
            
        except gspread.exceptions.SpreadsheetNotFound:
            raise RuntimeError(
                f"SPREADSHEET_NOT_FOUND: No se encontró la hoja de cálculo con ID {self.sheet_id}. "
                "Verifica que el ID sea correcto y que la cuenta de servicio tenga acceso."
            )
        except gspread.exceptions.WorksheetNotFound:
            raise RuntimeError(
                f"WORKSHEET_NOT_FOUND: No se encontró la hoja del catálogo. "
                "Verifica que la hoja exista y que el GID sea correcto."
            )
        except gspread.exceptions.APIError as e:
            error_msg = str(e).lower()
            if "permission" in error_msg or "denied" in error_msg:
                raise RuntimeError(
                    "PERMISSION_DENIED: No tienes permisos para acceder a esta hoja. "
                    "Verifica que la cuenta de servicio tenga acceso de lectura."
                )
            else:
                raise RuntimeError(f"Error del API de Google Sheets: {e}")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo catálogo: {e}")
            raise RuntimeError(f"Error inesperado: {e}")
    
    def obtener_estado_catalogo(self):
        """
        Obtiene información del estado del catálogo
        """
        try:
            # Verificar conexión
            test_cell = self.worksheet.acell('A1').value
            
            # Obtener información básica
            all_values = self.worksheet.get_all_values()
            
            return {
                "success": True,
                "conectado": True,
                "nombre_hoja": self.worksheet.title,
                "total_filas": len(all_values),
                "total_columnas": len(all_values[0]) if all_values else 0,
                "headers": all_values[0] if all_values else [],
                "url": f"https://docs.google.com/spreadsheets/d/{self.sheet_id}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "conectado": False,
                "error": str(e)
            }

# Función de compatibilidad para mantener la API existente
def obtener_catalogo():
    """
    Función de compatibilidad que usa la nueva clase CatalogService
    """
    try:
        service = CatalogService()
        return service.obtener_catalogo()
    except Exception as e:
        logger.error(f"Error en obtener_catalogo(): {e}")
        raise
