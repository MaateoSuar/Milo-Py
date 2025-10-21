import os
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict

logger = logging.getLogger(__name__)

TIPO_SHEET_ID = "1QG8a6yHmad5sFpVcKhC3l0oEAcjJftmHV2KAF56bkkM"
TIPO_GID = 1664309383

class TipoService:
    def __init__(self):
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
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
                # Fallback a archivo local si existe
                if os.path.exists("google_credentials.json"):
                    with open("google_credentials.json", "r", encoding="utf-8") as f:
                        credentials = json.load(f)
                        logger.info("Credenciales cargadas desde archivo local")
            if not isinstance(credentials, dict) or not credentials:
                raise ValueError("No se encontraron credenciales válidas para TipoService")
            if isinstance(credentials.get("private_key"), str):
                credentials["private_key"] = credentials["private_key"].replace("\\n", "\n")

            self.client = gspread.service_account_from_dict(credentials)
            self.spreadsheet = self.client.open_by_key(TIPO_SHEET_ID)
            self.worksheet = self.spreadsheet.get_worksheet_by_id(TIPO_GID)
            if not self.worksheet:
                raise RuntimeError(f"No se encontró la hoja con GID {TIPO_GID}")
            self._cache: Dict[str, str] = {}
        except Exception as e:
            logger.error(f"Error inicializando TipoService: {e}")
            raise

    def _find_col(self, headers, candidates):
        lower = [ (h or '').strip().lower() for h in headers ]
        for cand in candidates:
            c = cand.strip().lower()
            # exacto
            for i, h in enumerate(lower):
                if h == c:
                    return i
            # parcial
            for i, h in enumerate(lower):
                if c in h or h in c:
                    return i
        return None

    def _ensure_cache(self):
        if self._cache:
            return
        values = self.worksheet.get_all_values()
        if not values:
            return
        # 1) Modo estricto según estructura pedida: ID en columna I (idx 8), Tipo en columna E (idx 4), desde fila 4
        try:
            col_id = 8  # I
            col_tipo = 4  # E
            added = 0
            for idx, row in enumerate(values, start=1):
                if idx < 4:
                    continue
                if len(row) <= max(col_id, col_tipo):
                    continue
                id_raw = (row[col_id] or '').strip()
                tipo_val = (row[col_tipo] or '').strip()
                if not id_raw or not tipo_val:
                    continue
                key = id_raw.upper()
                self._cache[key] = tipo_val
                added += 1
            if added > 0:
                return
        except Exception:
            pass

        # 2) Fallback: detección por headers flexibles
        headers = values[0]
        idx_id = self._find_col(headers, ["id", "codigo", "código", "sku", "producto_id"])  # ID columna
        idx_tipo = self._find_col(headers, ["tipo", "category", "categoria", "categoría"])   # Tipo columna
        if idx_tipo is None:
            logger.warning("No se encontró columna 'Tipo' en la hoja de tipos (fallback)")
            return
        idx_concepto = self._find_col(headers, ["concepto"]) if idx_id is None else None

        for row in values[1:]:
            try:
                if len(row) <= idx_tipo:
                    continue
                tipo_val = (row[idx_tipo] or '').strip()
                if not tipo_val:
                    continue
                key = None
                if idx_id is not None and len(row) > idx_id:
                    key = (row[idx_id] or '').strip().upper()
                elif idx_concepto is not None and len(row) > idx_concepto:
                    key = (row[idx_concepto] or '').strip().upper()
                if key:
                    self._cache[key] = tipo_val
            except Exception:
                continue

    def obtener_tipo_por_id(self, id_val: str) -> str:
        try:
            if not id_val:
                return ""
            self._ensure_cache()
            return self._cache.get(str(id_val).strip().upper(), "")
        except Exception as e:
            logger.warning(f"No se pudo obtener tipo para ID {id_val}: {e}")
            return ""
