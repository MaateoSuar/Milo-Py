import requests
import json
import logging
from config import GOOGLE_SHEETS_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def obtener_catalogo():
    """
    Descarga el catálogo desde Google Sheets y devuelve un dict {ID: Nombre}
    """
    try:
        logger.info("Descargando catálogo desde Google Sheets...")
        
        # Construir URL desde configuración
        sheet_id = GOOGLE_SHEETS_CONFIG["SHEET_ID"]
        gid = GOOGLE_SHEETS_CONFIG["GID"]
        timeout = GOOGLE_SHEETS_CONFIG["TIMEOUT"]
        
        gviz_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?gid={gid}"
        
        r = requests.get(gviz_url, timeout=timeout)
        
        if r.status_code != 200:
            logger.error(f"Error HTTP {r.status_code} al acceder a Google Sheets")
            raise RuntimeError(f"No se pudo acceder a Google Sheets (HTTP {r.status_code})")

        # Elimina el prefijo/sufijo raro de Google
        texto = r.text
        if not texto.startswith("/*O_o*/"):
            logger.error("Respuesta inesperada de Google Sheets")
            raise RuntimeError("Formato de respuesta inesperado de Google Sheets")
            
        json_str = texto[47:-2]
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            raise RuntimeError("Error parseando respuesta de Google Sheets")

        if "table" not in data or "cols" not in data["table"]:
            logger.error("Estructura de datos inesperada")
            raise RuntimeError("Estructura de datos inesperada en Google Sheets")

        cols = [c["label"].strip() if c and "label" in c else "" for c in data["table"]["cols"]]
        logger.info(f"Columnas encontradas: {cols}")
        
        idx_id = next((i for i, c in enumerate(cols) if c.lower() == "id"), None)
        idx_nombre = next((i for i, c in enumerate(cols) if "nombre" in c.lower()), None)

        if idx_id is None or idx_nombre is None:
            logger.error(f"No se encontraron columnas ID/Nombre. ID: {idx_id}, Nombre: {idx_nombre}")
            raise RuntimeError("No se encontraron columnas ID/Nombre en el Sheets")

        catalogo = {}
        rows_processed = 0
        
        for row in data["table"]["rows"]:
            c = row.get("c", [])
            if not c: 
                continue
                
            id_val = c[idx_id]["v"] if idx_id < len(c) and c[idx_id] else None
            nombre_val = c[idx_nombre]["v"] if idx_nombre < len(c) and c[idx_nombre] else None
            
            if id_val and nombre_val:
                id_clean = str(id_val).strip().upper()
                nombre_clean = str(nombre_val).strip()
                catalogo[id_clean] = nombre_clean
                rows_processed += 1

        logger.info(f"Catálogo procesado: {len(catalogo)} productos de {rows_processed} filas")
        return catalogo

    except requests.RequestException as e:
        logger.error(f"Error de conexión: {e}")
        raise RuntimeError(f"Error de conexión: {e}")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise RuntimeError(f"Error inesperado: {e}")
