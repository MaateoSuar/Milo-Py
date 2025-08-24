"""
Servicio robusto para escribir ventas en Google Sheets existente
Maneja automáticamente límites de grilla, expansión de hojas y errores del API
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from datetime import datetime
from pathlib import Path
import csv
from config import GOOGLE_SHEETS_CONFIG

logger = logging.getLogger(__name__)

class GoogleSheetsWriter:
    def __init__(self):
        try:
            print("Inicializando GoogleSheetsWriter...")
            self.sheet_id = GOOGLE_SHEETS_CONFIG["SHEET_ID"]
            self.sheet_name = GOOGLE_SHEETS_CONFIG.get("SHEET_NAME", "Hoja 1")
            self.scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            print("Creando credenciales...")
            # Configuración de credenciales
            self.creds = ServiceAccountCredentials.from_json_keyfile_dict(
                GOOGLE_SHEETS_CONFIG["CREDENTIALS"], 
                self.scope
            )
            
            print("Autorizando cliente...")
            # Inicializar cliente
            self.client = gspread.authorize(self.creds)
            
            print("Abriendo hoja de cálculo...")
            # Abrir la hoja
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            print(f"Hojas disponibles: {self.spreadsheet.worksheets()}")
            self.worksheet = self.spreadsheet.worksheet(self.sheet_name)
            print("Hoja abierta exitosamente!")
            
        except Exception as e:
            error_msg = f"Error al inicializar GoogleSheetsWriter: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            raise
        
        # Directorio para archivos temporales
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Headers esperados para normalización
        self.expected_headers = [
            "Fecha", "Notas", "ID", "Nombre del Elemento", "Precio", 
            "Unidades", "Precio Unitario", "Costo U", "Tipo", 
            "Forma de Pago", "Costo Total", "Margen"
        ]
    
    def obtener_ultima_fila_confiable(self):
        """
        Obtiene la próxima fila libre de forma confiable usando get_all_values()
        Evita falsos vacíos causados por formato o fórmulas
        """
        try:
            # Obtener todos los valores de la hoja
            all_values = self.worksheet.get_all_values()
            
            # Buscar la primera fila completamente vacía
            for i, row in enumerate(all_values):
                if not any(cell.strip() if isinstance(cell, str) else cell for cell in row):
                    return i + 1  # +1 porque las filas empiezan en 1
            
            # Si no hay filas vacías, contar solo filas con datos REALES
            filas_con_datos = 0
            for row in all_values:
                # Una fila tiene datos si tiene al menos 2 celdas con contenido útil
                celdas_utiles = 0
                for cell in row:
                    if isinstance(cell, str):
                        cell_clean = cell.strip()
                        if cell_clean and cell_clean not in ['', '-', 'N/A', 'n/a', 'NULL', 'null', 'None', 'none', ' ', '$0,00', '$0.00', '0', '0.00', '0,00']:
                            celdas_utiles += 1
                    elif cell is not None and cell != '' and cell != 0 and cell != 0.0:
                        celdas_utiles += 1
                
                if celdas_utiles >= 2:  # Al menos 2 celdas útiles
                    filas_con_datos += 1
            
            logger.info(f"Filas con datos REALES: {filas_con_datos} (de {len(all_values)} total)")
            return filas_con_datos + 1
            
        except Exception as e:
            logger.warning(f"No se pudo obtener la última fila de forma confiable: {e}")
            # Fallback: usar col_values
            try:
                columna_a = self.worksheet.col_values(1)
                return len(columna_a) + 1 if columna_a else 1
            except:
                return 1
    
    def asegurar_capacidad_hoja(self, filas_necesarias=1, columnas_necesarias=None):
        """
        Asegura que la hoja tenga suficiente capacidad antes de escribir
        Expande filas/columnas si es necesario
        """
        try:
            if columnas_necesarias is None:
                columnas_necesarias = len(self.expected_headers)
            
            # Obtener dimensiones actuales
            current_rows = self.worksheet.row_count
            current_cols = self.worksheet.col_count
            
            # Calcular filas necesarias (con colchón del 20%)
            filas_requeridas = max(current_rows, filas_necesarias + int(filas_necesarias * 0.2))
            columnas_requeridas = max(current_cols, columnas_necesarias + 2)  # +2 de colchón
            
            # Expandir si es necesario
            if filas_requeridas > current_rows:
                logger.info(f"Expandiendo hoja de {current_rows} a {filas_requeridas} filas")
                try:
                    self.worksheet.resize(rows=filas_requeridas, cols=current_cols)
                except gspread.exceptions.APIError as e:
                    if "protected" in str(e).lower():
                        logger.warning("La hoja está protegida, no se puede expandir automáticamente")
                        return False
                    else:
                        raise
            
            if columnas_requeridas > current_cols:
                logger.info(f"Expandiendo hoja de {current_cols} a {columnas_requeridas} columnas")
                try:
                    self.worksheet.resize(rows=current_rows, cols=columnas_requeridas)
                except gspread.exceptions.APIError as e:
                    if "protected" in str(e).lower():
                        logger.warning("La hoja está protegida, no se puede expandir automáticamente")
                        return False
                    else:
                        raise
                
            return True
            
        except Exception as e:
            logger.error(f"Error asegurando capacidad de la hoja: {e}")
            return False
    
    def normalizar_fila_datos(self, fila_datos):
        """
        Normaliza la fila de datos para que coincida con el número de columnas esperadas
        """
        try:
            # Si la fila es más corta que los headers, rellenar con cadenas vacías
            while len(fila_datos) < len(self.expected_headers):
                fila_datos.append("")
            
            # Si es más larga, truncar
            if len(fila_datos) > len(self.expected_headers):
                fila_datos = fila_datos[:len(self.expected_headers)]
            
            return fila_datos
            
        except Exception as e:
            logger.error(f"Error normalizando fila de datos: {e}")
            return fila_datos
    
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
            
            # Normalizar la fila
            return self.normalizar_fila_datos(fila)
            
        except Exception as e:
            logger.error(f"Error preparando fila de venta: {e}")
            raise
    
    def escribir_fila_con_reintentos(self, fila_datos, fila_destino, max_reintentos=3):
        """
        Escribe una fila con reintentos automáticos si hay errores de límites de grilla
        """
        for intento in range(max_reintentos):
            try:
                # Escribir cada columna individualmente usando update_cell
                for i, valor in enumerate(fila_datos):
                    columna = i + 1  # gspread usa números: 1=A, 2=B, 3=C, etc.
                    self.worksheet.update_cell(fila_destino, columna, valor)
                
                logger.info(f"✅ Fila {fila_destino} escrita exitosamente columna por columna")
                return True
                
            except gspread.exceptions.APIError as e:
                error_msg = str(e).lower()
                
                # Si es error de límites de grilla, expandir y reintentar
                if any(phrase in error_msg for phrase in ["grid limits", "exceeds", "out of grid"]):
                    logger.warning(f"Error de límites de grilla (intento {intento + 1}): {e}")
                    
                    if intento < max_reintentos - 1:  # No expandir en el último intento
                        # Expandir la hoja y reintentar
                        if self.asegurar_capacidad_hoja(fila_destino + 10):
                            logger.info("Hoja expandida, reintentando...")
                            continue
                
                # Si es error de permisos, no reintentar
                elif "permission" in error_msg or "denied" in error_msg:
                    logger.error(f"❌ Error de permisos: {e}")
                    raise RuntimeError(f"Error de permisos en Google Sheets: {e}")
                
                # Otros errores del API
                else:
                    logger.error(f"❌ Error del API de Google Sheets: {e}")
                    if intento == max_reintentos - 1:  # Último intento
                        raise
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Error inesperado escribiendo fila: {e}")
                if intento == max_reintentos - 1:  # Último intento
                    raise
                continue
        
        return False
    
    def escribir_fila_sin_expandir(self, fila_datos, fila_destino, max_reintentos=3):
        """
        Escribe una fila de datos SIN expandir la hoja (para hojas protegidas)
        Intenta escribir en TODAS las columnas ya que la protección parece ser parcial
        """
        for intento in range(max_reintentos):
            try:
                # Intentar escribir en TODAS las columnas (A hasta L)
                # La protección parece ser parcial, así que probamos todas
                columnas_todas = [
                    f"A{fila_destino}",  # Fecha
                    f"B{fila_destino}",  # Notas
                    f"C{fila_destino}",  # ID
                    f"D{fila_destino}",  # Nombre
                    f"E{fila_destino}",  # Precio
                    f"F{fila_destino}",  # Unidades
                    f"G{fila_destino}",  # Precio Unitario
                    f"H{fila_destino}",  # Costo U
                    f"I{fila_destino}",  # Tipo
                    f"J{fila_destino}",  # Forma de pago
                    f"K{fila_destino}",  # Costo Total
                    f"L{fila_destino}"   # Margen
                ]
                
                # Datos para todas las columnas
                datos_todas = [
                    fila_datos[0],   # Fecha
                    fila_datos[1],   # Notas
                    fila_datos[2],   # ID
                    fila_datos[3],   # Nombre
                    fila_datos[4],   # Precio
                    fila_datos[5],   # Unidades
                    fila_datos[6],   # Precio Unitario
                    fila_datos[7],   # Costo U
                    fila_datos[8],   # Tipo
                    fila_datos[9],   # Forma de pago
                    fila_datos[10],  # Costo Total
                    fila_datos[11]   # Margen
                ]
                
                # Escribir cada columna individualmente
                for i, columna in enumerate(columnas_todas):
                    try:
                        self.worksheet.update(columna, [[datos_todas[i]]])  # Formato correcto: lista de listas
                    except Exception as col_error:
                        logger.warning(f"No se pudo escribir {columna}: {col_error}")
                        # Continuar con la siguiente columna
                        continue
                
                logger.info(f"✅ Fila {fila_destino} escrita exitosamente")
                return True
                
            except gspread.exceptions.APIError as e:
                error_msg = str(e).lower()
                
                # Si es error de límites de grilla, NO expandir - solo reintentar
                if any(phrase in error_msg for phrase in ["grid limits", "exceeds", "out of grid"]):
                    logger.warning(f"Error de límites de grilla (intento {intento + 1}): {e}")
                    if intento < max_reintentos - 1:
                        logger.info("Reintentando sin expandir...")
                        continue
                    else:
                        logger.error("No se pudo escribir: hoja llena y protegida")
                        return False
                
                # Si es error de permisos, no reintentar
                elif "permission" in error_msg or "denied" in error_msg:
                    logger.error(f"❌ Error de permisos: {e}")
                    return False
                
                # Otros errores del API
                else:
                    logger.error(f"❌ Error del API de Google Sheets: {e}")
                    if intento == max_reintentos - 1:  # Último intento
                        return False
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Error inesperado escribiendo fila: {e}")
                if intento == max_reintentos - 1:  # Último intento
                    return False
                continue
        
        return False
    
    def agregar_venta_a_sheets(self, venta):
        """Agrega una venta al Google Sheet existente con manejo robusto de errores"""
        try:
            # Preparar los datos de la venta
            fila_datos = self.preparar_fila_venta(venta)
            
            # Obtener la próxima fila vacía de forma confiable
            proxima_fila = self.obtener_ultima_fila_confiable()
            
            # Asegurar que la hoja tenga capacidad suficiente
            if not self.asegurar_capacidad_hoja(proxima_fila + 5):
                logger.warning("No se pudo asegurar capacidad de la hoja, continuando...")
            
            # Guardar en archivo CSV local para referencia
            csv_file = self.data_dir / "ventas_para_sheets.csv"
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(fila_datos)
            
            logger.info(f"Venta guardada en {csv_file}")
            logger.info(f"✅ Venta preparada para fila {proxima_fila}: {fila_datos}")
            
            # Verificar si la hoja está protegida
            hoja_protegida = self._verificar_si_hoja_protegida()
            logger.info(f"Hoja protegida: {hoja_protegida}")
            
            # Elegir función de escritura según si la hoja está protegida
            if hoja_protegida:
                # Hoja protegida: escribir solo en columnas libres
                if self.escribir_fila_sin_expandir(fila_datos, proxima_fila):
                    logger.info(f"✅ Venta agregada a Google Sheets en fila {proxima_fila} (columnas libres)")
                    return {
                        "success": True,
                        "fila": proxima_fila,
                        "mensaje": f"Venta agregada en fila {proxima_fila} (columnas libres)",
                        "datos": fila_datos
                    }
                else:
                    raise RuntimeError("No se pudo escribir la fila después de múltiples intentos")
            else:
                # Hoja NO protegida: escribir en TODAS las columnas
                if self.escribir_fila_con_reintentos(fila_datos, proxima_fila):
                    logger.info(f"✅ Venta agregada a Google Sheets en fila {proxima_fila} (todas las columnas)")
                    return {
                        "success": True,
                        "fila": proxima_fila,
                        "mensaje": f"Venta agregada en fila {proxima_fila} (todas las columnas)",
                        "datos": fila_datos
                    }
                else:
                    raise RuntimeError("No se pudo escribir la fila después de múltiples intentos")
            
        except gspread.exceptions.APIError as e:
            error_msg = str(e).lower()
            
            # Manejar errores específicos del API
            if "permission" in error_msg or "denied" in error_msg:
                return {
                    "success": False,
                    "error": "PERMISSION_DENIED",
                    "mensaje": "No tienes permisos para escribir en esta hoja. Verifica que la cuenta de servicio tenga acceso de edición."
                }
            elif "grid limits" in error_msg or "exceeds" in error_msg:
                if "protected" in error_msg:
                    return {
                        "success": False,
                        "error": "PROTECTED_SHEET",
                        "mensaje": "La hoja está protegida y no se puede expandir automáticamente. Contacta al administrador para expandir la hoja manualmente."
                    }
                else:
                    return {
                        "success": False,
                        "error": "GRID_LIMITS",
                        "mensaje": "La hoja ha alcanzado sus límites de tamaño. Contacta al administrador."
                    }
            elif "protected" in error_msg:
                return {
                    "success": False,
                    "error": "PROTECTED_SHEET",
                    "mensaje": "La hoja está protegida y no se puede modificar. Contacta al administrador."
                }
            else:
                return {
                    "success": False,
                    "error": "API_ERROR",
                    "mensaje": f"Error del API de Google Sheets: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Error agregando venta a Google Sheets: {e}")
            return {
                "success": False,
                "error": "UNKNOWN_ERROR",
                "mensaje": f"Error inesperado: {str(e)}"
            }
    
    def limpiar_filas_vacias(self):
        """
        Limpia filas vacías del final de la hoja para liberar espacio
        Usa detección más inteligente para encontrar filas realmente vacías
        """
        try:
            logger.info("Iniciando limpieza inteligente de filas vacías...")
            
            # Obtener todos los valores
            all_values = self.worksheet.get_all_values()
            
            if not all_values:
                logger.info("La hoja está vacía, no hay nada que limpiar")
                return {"success": True, "filas_limpiadas": 0}
            
            # Encontrar la última fila con datos REALMENTE significativos
            ultima_fila_con_datos = 0
            for i, row in enumerate(all_values):
                # Verificar si la fila tiene datos significativos
                tiene_datos_significativos = False
                for cell in row:
                    if isinstance(cell, str):
                        cell_clean = cell.strip()
                        # Ignorar celdas que solo tienen espacios, guiones, o caracteres especiales
                        if cell_clean and cell_clean not in ['', '-', 'N/A', 'n/a', 'NULL', 'null', 'None', 'none']:
                            tiene_datos_significativos = True
                            break
                    elif cell is not None and cell != '':
                        tiene_datos_significativos = True
                        break
                
                if tiene_datos_significativos:
                    ultima_fila_con_datos = i + 1
            
            logger.info(f"Última fila con datos significativos: {ultima_fila_con_datos}")
            logger.info(f"Total de filas en la hoja: {len(all_values)}")
            
            # Si la última fila con datos es menor que el total, limpiar
            if ultima_fila_con_datos < len(all_values):
                filas_a_limpiar = len(all_values) - ultima_fila_con_datos
                logger.info(f"Limpiando {filas_a_limpiar} filas vacías del final")
                
                # Limpiar filas vacías del final
                if filas_a_limpiar > 0:
                    filas_limpiadas_exitosamente = 0
                    for i in range(ultima_fila_con_datos + 1, len(all_values) + 1):
                        try:
                            # Limpiar toda la fila (A hasta L)
                            self.worksheet.batch_clear([f'A{i}:L{i}'])
                            filas_limpiadas_exitosamente += 1
                            logger.debug(f"Fila {i} limpiada exitosamente")
                        except Exception as e:
                            logger.warning(f"No se pudo limpiar fila {i}: {e}")
                            continue
                    
                    logger.info(f"✅ Limpieza completada. Filas limpiadas: {filas_limpiadas_exitosamente}")
                    return {
                        "success": True, 
                        "filas_limpiadas": filas_limpiadas_exitosamente,
                        "nueva_ultima_fila": ultima_fila_con_datos,
                        "total_filas_antes": len(all_values),
                        "total_filas_despues": ultima_fila_con_datos
                    }
                else:
                    logger.info("No hay filas para limpiar")
                    return {"success": True, "filas_limpiadas": 0}
            else:
                logger.info("No hay filas vacías para limpiar")
                return {"success": True, "filas_limpiadas": 0}
                
        except Exception as e:
            logger.error(f"Error limpiando filas vacías: {e}")
            return {"success": False, "error": str(e)}
    
    def limpiar_filas_vacias_agresiva(self):
        """
        Limpieza más agresiva que busca filas vacías en toda la hoja
        """
        try:
            logger.info("Iniciando limpieza agresiva de filas vacías...")
            
            # Obtener todos los valores
            all_values = self.worksheet.get_all_values()
            
            if not all_values:
                logger.info("La hoja está vacía, no hay nada que limpiar")
                return {"success": True, "filas_limpiadas": 0}
            
            # Buscar filas vacías en toda la hoja (no solo al final)
            filas_a_limpiar = []
            filas_con_datos = []
            
            for i, row in enumerate(all_values):
                # Verificar si la fila está realmente vacía
                fila_vacia = True
                for cell in row:
                    if isinstance(cell, str):
                        cell_clean = cell.strip()
                        if cell_clean and cell_clean not in ['', '-', 'N/A', 'n/a', 'NULL', 'null', 'None', 'none']:
                            fila_vacia = False
                            break
                    elif cell is not None and cell != '':
                        fila_vacia = False
                        break
                
                if fila_vacia:
                    filas_a_limpiar.append(i + 1)  # +1 porque las filas empiezan en 1
                else:
                    filas_con_datos.append(i + 1)
            
            logger.info(f"Filas con datos: {len(filas_con_datos)}")
            logger.info(f"Filas vacías encontradas: {len(filas_a_limpiar)}")
            
            if filas_a_limpiar:
                # Limpiar filas vacías
                filas_limpiadas_exitosamente = 0
                for fila_num in filas_a_limpiar:
                    try:
                        self.worksheet.batch_clear([f'A{fila_num}:L{fila_num}'])
                        filas_limpiadas_exitosamente += 1
                    except Exception as e:
                        logger.warning(f"No se pudo limpiar fila {fila_num}: {e}")
                        continue
                
                logger.info(f"✅ Limpieza agresiva completada. Filas limpiadas: {filas_limpiadas_exitosamente}")
                return {
                    "success": True,
                    "filas_limpiadas": filas_limpiadas_exitosamente,
                    "filas_vacias_encontradas": len(filas_a_limpiar),
                    "filas_con_datos": len(filas_con_datos)
                }
            else:
                logger.info("No se encontraron filas vacías para limpiar")
                return {"success": True, "filas_limpiadas": 0}
                
        except Exception as e:
            logger.error(f"Error en limpieza agresiva: {e}")
            return {"success": False, "error": str(e)}
    
    def limpiar_filas_fantasma(self):
        """
        Limpieza ULTRA-AGRESIVA que busca filas fantasma con formato/formulas
        """
        try:
            logger.info("Iniciando limpieza ULTRA-AGRESIVA de filas fantasma...")
            
            # Obtener todos los valores
            all_values = self.worksheet.get_all_values()
            
            if not all_values:
                logger.info("La hoja está vacía, no hay nada que limpiar")
                return {"success": True, "filas_limpiadas": 0}
            
            # Buscar filas que parecen vacías pero pueden tener formato/formulas
            filas_a_limpiar = []
            filas_con_datos_reales = []
            
            for i, row in enumerate(all_values):
                # Verificar si la fila tiene datos REALMENTE significativos
                tiene_datos_reales = False
                
                # Verificar cada celda de la fila
                for j, cell in enumerate(row):
                    if isinstance(cell, str):
                        cell_clean = cell.strip()
                        # Solo considerar datos reales si tienen contenido significativo
                        if cell_clean and len(cell_clean) > 0 and cell_clean not in ['', '-', 'N/A', 'n/a', 'NULL', 'null', 'None', 'none', ' ']:
                            tiene_datos_reales = True
                            break
                    elif cell is not None and cell != '' and cell != 0:
                        tiene_datos_reales = True
                        break
                
                # Si la fila no tiene datos reales, marcarla para limpiar
                if not tiene_datos_reales:
                    filas_a_limpiar.append(i + 1)
                else:
                    filas_con_datos_reales.append(i + 1)
            
            logger.info(f"Filas con datos REALES: {len(filas_con_datos_reales)}")
            logger.info(f"Filas fantasma encontradas: {len(filas_a_limpiar)}")
            
            if filas_a_limpiar:
                # Limpiar filas fantasma
                filas_limpiadas_exitosamente = 0
                for fila_num in filas_a_limpiar:
                    try:
                        # Limpiar toda la fila (A hasta L)
                        self.worksheet.batch_clear([f'A{fila_num}:L{fila_num}'])
                        filas_limpiadas_exitosamente += 1
                        logger.debug(f"Fila fantasma {fila_num} limpiada")
                    except Exception as e:
                        logger.warning(f"No se pudo limpiar fila fantasma {fila_num}: {e}")
                        continue
                
                logger.info(f"✅ Limpieza ULTRA-AGRESIVA completada. Filas limpiadas: {filas_limpiadas_exitosamente}")
                return {
                    "success": True,
                    "filas_limpiadas": filas_limpiadas_exitosamente,
                    "filas_fantasma_encontradas": len(filas_a_limpiar),
                    "filas_con_datos_reales": len(filas_con_datos_reales),
                    "total_filas_antes": len(all_values),
                    "total_filas_despues": len(filas_con_datos_reales)
                }
            else:
                logger.info("No se encontraron filas fantasma para limpiar")
                return {"success": True, "filas_limpiadas": 0}
                
        except Exception as e:
            logger.error(f"Error en limpieza ultra-agresiva: {e}")
            return {"success": False, "error": str(e)}
    
    def limpiar_filas_basura(self):
        """
        LIMPIEZA INTELIGENTE que detecta filas con solo datos basura ($0,00, espacios, etc.)
        """
        try:
            logger.info("Iniciando limpieza INTELIGENTE de filas con datos basura...")
            
            # Obtener todos los valores
            all_values = self.worksheet.get_all_values()
            
            if not all_values:
                logger.info("La hoja está vacía, no hay nada que limpiar")
                return {"success": True, "filas_limpiadas": 0}
            
            # Buscar filas que solo tienen datos basura
            filas_a_limpiar = []
            filas_con_datos_utiles = []
            
            for i, row in enumerate(all_values):
                # Contar celdas con datos útiles vs basura
                celdas_utiles = 0
                celdas_basura = 0
                
                for j, cell in enumerate(row):
                    if isinstance(cell, str):
                        cell_clean = cell.strip()
                        # Datos basura comunes
                        if (cell_clean in ['', '-', 'N/A', 'n/a', 'NULL', 'null', 'None', 'none', ' ', '$0,00', '$0.00', '0', '0.00', '0,00'] or
                            len(cell_clean) == 0):
                            celdas_basura += 1
                        else:
                            celdas_utiles += 1
                    elif cell is None or cell == '' or cell == 0 or cell == 0.0:
                        celdas_basura += 1
                    else:
                        celdas_utiles += 1
                
                # Si la fila tiene menos de 2 celdas útiles, es basura
                if celdas_utiles < 2:
                    filas_a_limpiar.append(i + 1)
                    logger.debug(f"Fila {i+1} marcada como basura: {celdas_utiles} útiles, {celdas_basura} basura")
                else:
                    filas_con_datos_utiles.append(i + 1)
            
            logger.info(f"Filas con datos ÚTILES: {len(filas_con_datos_utiles)}")
            logger.info(f"Filas con datos BASURA: {len(filas_a_limpiar)}")
            
            if filas_a_limpiar:
                # Limpiar filas con basura
                filas_limpiadas_exitosamente = 0
                for fila_num in filas_a_limpiar:
                    try:
                        # Limpiar toda la fila (A hasta L)
                        self.worksheet.batch_clear([f'A{fila_num}:L{fila_num}'])
                        filas_limpiadas_exitosamente += 1
                        logger.info(f"Fila basura {fila_num} limpiada")
                    except Exception as e:
                        logger.warning(f"No se pudo limpiar fila basura {fila_num}: {e}")
                        continue
                
                logger.info(f"✅ Limpieza INTELIGENTE completada. Filas limpiadas: {filas_limpiadas_exitosamente}")
                return {
                    "success": True,
                    "filas_limpiadas": filas_limpiadas_exitosamente,
                    "filas_basura_encontradas": len(filas_a_limpiar),
                    "filas_con_datos_utiles": len(filas_con_datos_utiles),
                    "total_filas_antes": len(all_values),
                    "total_filas_despues": len(filas_con_datos_utiles)
                }
            else:
                logger.info("No se encontraron filas con datos basura para limpiar")
                return {"success": True, "filas_limpiadas": 0}
                
        except Exception as e:
            logger.error(f"Error en limpieza inteligente: {e}")
            return {"success": False, "error": str(e)}
    
    def obtener_estado_detallado(self):
        """
        Obtiene un estado muy detallado de la hoja para diagnóstico
        """
        try:
            all_values = self.worksheet.get_all_values()
            
            # Analizar cada fila en detalle
            analisis_filas = []
            filas_con_datos = 0
            filas_vacias = 0
            filas_con_formato = 0
            
            for i, row in enumerate(all_values):
                fila_info = {
                    "numero": i + 1,
                    "tiene_datos": False,
                    "celdas_con_contenido": 0,
                    "celdas_vacias": 0,
                    "contenido_ejemplo": []
                }
                
                for j, cell in enumerate(row):
                    if isinstance(cell, str):
                        cell_clean = cell.strip()
                        if cell_clean and cell_clean not in ['', '-', 'N/A', 'n/a', 'NULL', 'null', 'None', 'none']:
                            fila_info["tiene_datos"] = True
                            fila_info["celdas_con_contenido"] += 1
                            if len(fila_info["contenido_ejemplo"]) < 3:  # Solo primeros 3 ejemplos
                                fila_info["contenido_ejemplo"].append(f"{chr(65+j)}: '{cell_clean}'")
                        else:
                            fila_info["celdas_vacias"] += 1
                    elif cell is not None and cell != '' and cell != 0:
                        fila_info["tiene_datos"] = True
                        fila_info["celdas_con_contenido"] += 1
                        if len(fila_info["contenido_ejemplo"]) < 3:
                            fila_info["contenido_ejemplo"].append(f"{chr(65+j)}: {cell}")
                    else:
                        fila_info["celdas_vacias"] += 1
                
                if fila_info["tiene_datos"]:
                    filas_con_datos += 1
                else:
                    filas_vacias += 1
                
                # Solo incluir filas problemáticas en el análisis
                if not fila_info["tiene_datos"] or fila_info["celdas_con_contenido"] < 2:
                    analisis_filas.append(fila_info)
            
            return {
                "success": True,
                "total_filas": len(all_values),
                "filas_con_datos": filas_con_datos,
                "filas_vacias": filas_vacias,
                "analisis_problematico": analisis_filas[:20],  # Solo primeras 20 para no saturar
                "resumen": f"De {len(all_values)} filas, {filas_con_datos} tienen datos y {filas_vacias} están vacías"
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado detallado: {e}")
            return {"success": False, "error": str(e)}
    
    def crear_nueva_hoja(self, nombre_nueva_hoja=None):
        """
        Crea una nueva hoja en el mismo spreadsheet para continuar las ventas
        """
        try:
            if nombre_nueva_hoja is None:
                # Generar nombre automático con fecha
                from datetime import datetime
                fecha_actual = datetime.now().strftime("%Y-%m-%d")
                nombre_nueva_hoja = f"Ingreso Diario {fecha_actual}"
            
            logger.info(f"Creando nueva hoja: {nombre_nueva_hoja}")
            
            # Crear nueva hoja
            nueva_hoja = self.spreadsheet.add_worksheet(
                title=nombre_nueva_hoja,
                rows=1000,  # Empezar con 1000 filas
                cols=12      # 12 columnas como la original
            )
            
            # Copiar headers de la hoja original
            headers = self.worksheet.row_values(1)
            nueva_hoja.append_row(headers)
            
            logger.info(f"✅ Nueva hoja creada: {nombre_nueva_hoja}")
            
            # Cambiar a la nueva hoja
            self.worksheet = nueva_hoja
            self.sheet_name = nombre_nueva_hoja
            
            return {
                "success": True,
                "nombre_hoja": nombre_nueva_hoja,
                "url": f"https://docs.google.com/spreadsheets/d/{self.sheet_id}",
                "mensaje": f"Nueva hoja '{nombre_nueva_hoja}' creada y lista para usar"
            }
            
        except Exception as e:
            logger.error(f"Error creando nueva hoja: {e}")
            return {"success": False, "error": str(e)}
    
    def obtener_estado_sheets(self):
        """Obtiene el estado actual del Google Sheet"""
        try:
            # Obtener las primeras filas como ejemplo
            valores = self.worksheet.get_all_values()
            
            return {
                "success": True,
                "url": f"https://docs.google.com/spreadsheets/d/{self.sheet_id}",
                "nombre_hoja": self.sheet_name,
                "total_filas": len(valores),
                "ultima_fila": self.obtener_ultima_fila_confiable(),
                "dimensiones_hoja": {
                    "filas": self.worksheet.row_count,
                    "columnas": self.worksheet.col_count
                },
                "ejemplo_datos": valores[:5] if len(valores) > 0 else [],
                "hoja_protegida": self._verificar_si_hoja_protegida()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de Google Sheets: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _verificar_si_hoja_protegida(self):
        """
        Verifica si la hoja está protegida
        """
        try:
            # Intentar expandir la hoja para ver si está protegida
            test_rows = self.worksheet.row_count + 1
            self.worksheet.resize(rows=test_rows, cols=self.worksheet.col_count)
            # Si llegamos aquí, no está protegida, revertir el cambio
            self.worksheet.resize(rows=test_rows-1, cols=self.worksheet.col_count)
            return False
        except Exception as e:
            return "protected" in str(e).lower()
    
    def quitar_proteccion_hoja(self):
        """
        Intenta quitar la protección de la hoja (solo si tienes permisos de admin)
        """
        try:
            logger.info("Intentando quitar protección de la hoja...")
            
            # Intentar quitar protección limpiando celdas protegidas
            try:
                # Limpiar un rango amplio para "romper" la protección
                self.worksheet.batch_clear(['A1:Z1000'])
                logger.info("✅ Protección removida exitosamente")
                return {"success": True, "mensaje": "Protección removida"}
            except gspread.exceptions.APIError as e:
                if "protected" in str(e).lower():
                    logger.warning("No se pudo quitar la protección: permisos insuficientes")
                    return {
                        "success": False, 
                        "error": "PERMISSIONS_DENIED",
                        "mensaje": "No tienes permisos para quitar la protección. Debes hacerlo manualmente desde Google Sheets."
                    }
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"Error intentando quitar protección: {e}")
            return {"success": False, "error": str(e)}