import os
import json
from typing import List, Dict, Optional
import requests

from config import GOOGLE_APPS_SCRIPT

DEFAULT_TIMEOUT = 15

class GASClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: Optional[int] = None):
        self.base_url = base_url or GOOGLE_APPS_SCRIPT.get("GAS_URL", "").strip()
        self.api_key = api_key or GOOGLE_APPS_SCRIPT.get("GAS_API_KEY", "").strip()
        self.timeout = timeout or GOOGLE_APPS_SCRIPT.get("TIMEOUT", DEFAULT_TIMEOUT)

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def post_articulos(self, articulos: List[Dict]) -> Dict:
        """
        Envía artículos al Apps Script, con payload:
        { "articulos": [ { nombre, cantidad, precio, total }, ... ] }
        """
        if not self.is_configured():
            return {"success": False, "error": "GAS_URL no configurado"}

        payload = {"articulos": articulos}
        try:
            resp = requests.post(self.base_url, headers=self._headers(), data=json.dumps(payload), timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return {"success": data.get("status") == "success", "data": data}
        except requests.HTTPError as e:
            # capturar cuerpo para debug
            try:
                details = resp.text
            except Exception:
                details = str(e)
            return {"success": False, "error": f"HTTP {resp.status_code}", "details": details}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton simple
_gas_client: Optional[GASClient] = None

def get_gas_client() -> GASClient:
    global _gas_client
    if _gas_client is None:
        _gas_client = GASClient()
    return _gas_client
