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

    def _get_sheet_copia_codigos(self):
        """
        Devuelve la worksheet titulada "Copia de Códigos Stock" si existe (título exacto o ignorando acentos/mayúsculas).
        """
        ws = self._get_worksheet_by_title("Copia de Códigos Stock")
        return ws

    def _normalize_title(self, s: str) -> str:
        try:
            import unicodedata
            s_norm = unicodedata.normalize('NFKD', s)
            s_ascii = ''.join(ch for ch in s_norm if not unicodedata.combining(ch))
            return s_ascii.strip().lower()
        except Exception:
            return s.strip().lower()

    def _get_worksheet_by_title(self, title: str):
        """Obtiene una hoja por título ignorando acentos y mayúsculas/minúsculas"""
        try:
            wanted = self._normalize_title(str(title))
            for ws in self.spreadsheet.worksheets():
                if self._normalize_title(ws.title) == wanted:
                    return ws
        except Exception:
            pass
        return None
    
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

            # 1) Modo especial: hoja "Copia de Códigos Stock" usando columnas I (ID) y J (Nombre) desde fila 4
            try:
                ws_copia = self._get_sheet_copia_codigos()
            except Exception:
                ws_copia = None
            if ws_copia is not None:
                try:
                    values = ws_copia.get_all_values()
                    catalogo_especial = {}
                    # Columnas I y J son índices 8 y 9 (0-based)
                    col_i, col_j = 8, 9
                    for row_idx, row in enumerate(values, start=1):
                        if row_idx < 4:
                            continue  # empezar desde fila 4
                        # Asegurar longitud
                        if len(row) <= col_j:
                            continue
                        codigo_i = (row[col_i] or "").strip().upper()
                        nombre_j = (row[col_j] or "").strip()
                        if not codigo_i:
                            continue
                        # Normalizar espacios en el nombre (columna J). Si falta, usar el código como nombre.
                        nombre_clean = " ".join(nombre_j.split()) if nombre_j else codigo_i
                        catalogo_especial[codigo_i] = {"nombre": nombre_clean, "precio": 0.0}
                    if catalogo_especial:
                        logger.info(f"Catálogo (Copia de Códigos Stock): {len(catalogo_especial)} códigos desde I (ID) y J (Nombre)")
                        return catalogo_especial
                    else:
                        logger.warning("Hoja 'Copia de Códigos Stock' no produjo filas válidas (I+J)")
                except Exception as e:
                    logger.warning(f"Fallo leyendo 'Copia de Códigos Stock': {e}. Se usará modo estándar.")
            
            def parse_price_chilean(value_str: str) -> float:
                try:
                    if value_str is None:
                        return 0.0
                    v = str(value_str).replace('$', '').replace(' ', '').strip()
                    # Formato chileno: miles con punto, decimales con coma
                    if ',' in v and '.' in v:
                        # 11.600,00 -> 11600.00
                        v = v.replace('.', '').replace(',', '.')
                    elif ',' in v:
                        # 1,234 -> 1234  o  1234,56 -> 1234.56
                        # Si hay una sola coma, asumir decimales
                        parts = v.split(',')
                        if len(parts) == 2 and parts[1].isdigit():
                            v = parts[0].replace('.', '') + '.' + parts[1]
                        else:
                            v = v.replace(',', '')
                    else:
                        # Solo puntos: 11.600 -> 11600
                        # Si parece miles, quitar puntos
                        if v.count('.') >= 1 and (len(v.split('.')[-1]) != 3):
                            # Caso raro: dejar como está
                            pass
                        else:
                            v = v.replace('.', '')
                    return float(v) if v else 0.0
                except Exception:
                    return 0.0
            
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
            
            # 2) Modo estándar (fallback)
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
                        
                    # Limpiar y convertir el precio (formato chileno)
                    precio_float = parse_price_chilean(precio_val)

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

    def obtener_rangos_precios(self):
        """
        Lee la pestaña "Codigos Stock" y devuelve una lista de umbrales ordenados numéricamente
        según el número de rango en "Concepto":
          Concepto = "Rango de precio N"  -> valor en la columna adyacente

        Retorna: [rango1, rango2, rango3, ...] como floats
        """
        try:
            # Aceptar "Códigos Stock" o "Codigos Stock" (con/sin acento)
            ws = self._get_worksheet_by_title("Códigos Stock") or self._get_worksheet_by_title("Codigos Stock")
            if ws is None:
                raise RuntimeError("No se encontró la hoja 'Codigos Stock'")

            values = ws.get_all_values()
            if not values:
                return []

            import re
            rangos = []
            # Detectar "Rango de precio N" en cualquier columna y tomar valor de la columna siguiente
            for row_idx, row in enumerate(values, start=1):
                num_cols = len(row)
                for col_idx in range(num_cols):
                    concepto = (row[col_idx] or "").strip()
                    m = re.search(r"rango\s*de\s*precio\s*(\d+)", concepto, re.IGNORECASE)
                    if not m:
                        continue
                    numero = int(m.group(1))
                    # valor es la celda siguiente si existe; si no, buscar la primera no vacía a la derecha
                    valor_raw = ""
                    if col_idx + 1 < num_cols:
                        valor_raw = (row[col_idx + 1] or "").strip()
                    if not valor_raw:
                        for k in range(col_idx + 2, num_cols):
                            if row[k] and str(row[k]).strip():
                                valor_raw = str(row[k]).strip()
                                break

                    # Normalizar formato chileno
                    try:
                        v = str(valor_raw).replace('$', '').replace(' ', '').strip()
                        if ',' in v and '.' in v:
                            v = v.replace('.', '').replace(',', '.')
                        elif ',' in v:
                            parts = v.split(',')
                            if len(parts) == 2 and parts[1].isdigit():
                                v = parts[0].replace('.', '') + '.' + parts[1]
                            else:
                                v = v.replace(',', '')
                        else:
                            v = v.replace('.', '')
                        valor = float(v) if v else 0.0
                    except Exception:
                        valor = 0.0

                    rangos.append((numero, valor))

            # Ordenar por el número de rango y devolver solo los valores
            rangos.sort(key=lambda t: t[0])
            return [val for (_, val) in rangos]
        except Exception as e:
            logger.error(f"Error obteniendo rangos de precios: {e}")
            return []

    def obtener_rangos_por_grupo(self):
        """
        Devuelve un dict con umbrales por grupo/prefijo de código (A, AN, C, ...)
        Estructura esperada de filas (flexible): en alguna columna aparece "Rango de precio N",
        en otra columna de la MISMA fila aparece el código tipo A1/AN2/C3, y a la derecha del
        texto de rango aparece el valor con formato chileno ($11.600,00).
        Retorna: { "A": [0, 8000, 11600], "AN": [0, 7600, 8000], ... }
        """
        try:
            # Aceptar "Códigos Stock" o "Codigos Stock"
            ws = self._get_worksheet_by_title("Códigos Stock") or self._get_worksheet_by_title("Codigos Stock")
            if ws is None:
                raise RuntimeError("No se encontró la hoja 'Codigos Stock'")

            values = ws.get_all_values()
            if not values:
                return {}

            import re
            grupos_tmp = {}

            for row in values:
                num_cols = len(row)
                # Detectar rango en la fila
                rango_num = None
                rango_col_idx = None
                for col_idx in range(num_cols):
                    texto = (row[col_idx] or "").strip()
                    m = re.search(r"rango\s*de\s*precio\s*(\d+)", texto, re.IGNORECASE)
                    if m:
                        rango_num = int(m.group(1))
                        rango_col_idx = col_idx
                        break
                if rango_num is None:
                    continue

                # Buscar código tipo A1 / AN2 en la misma fila
                grupo_letras = None
                for col_idx in range(num_cols):
                    celda = (row[col_idx] or "").strip()
                    mcode = re.match(r"^([A-Za-z]+)(\d+)$", celda)
                    if mcode:
                        grupo_letras = mcode.group(1).upper()
                        break
                if not grupo_letras:
                    continue

                # Valor a la derecha del texto de rango
                valor_raw = ""
                if rango_col_idx + 1 < num_cols:
                    valor_raw = (row[rango_col_idx + 1] or "").strip()
                if not valor_raw:
                    for k in range(rango_col_idx + 2, num_cols):
                        if row[k] and str(row[k]).strip():
                            valor_raw = str(row[k]).strip()
                            break

                # Normalizar formato chileno
                try:
                    v = str(valor_raw).replace('$', '').replace(' ', '').strip()
                    if ',' in v and '.' in v:
                        v = v.replace('.', '').replace(',', '.')
                    elif ',' in v:
                        parts = v.split(',')
                        if len(parts) == 2 and parts[1].isdigit():
                            v = parts[0].replace('.', '') + '.' + parts[1]
                        else:
                            v = v.replace(',', '')
                    else:
                        v = v.replace('.', '')
                    valor = float(v) if v else 0.0
                except Exception:
                    valor = 0.0

                grupos_tmp.setdefault(grupo_letras, []).append((rango_num, valor))

            # Ordenar cada grupo por N y devolver solo valores
            resultado = {}
            for grupo, pares in grupos_tmp.items():
                pares.sort(key=lambda t: t[0])
                resultado[grupo] = [val for (_, val) in pares]

            return resultado
        except Exception as e:
            logger.error(f"Error obteniendo rangos de precios por grupo: {e}")
            return {}

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

def obtener_rangos():
    try:
        service = CatalogService()
        return service.obtener_rangos_por_grupo()
    except Exception as e:
        logger.error(f"Error en obtener_rangos(): {e}")
        return {}
