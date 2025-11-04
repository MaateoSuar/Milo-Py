import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import List, Dict, Any

# GAS Web App URL para EGRESOS
# Se puede configurar por env EGRESOS_GAS_URL
EGRESOS_GAS_URL = os.getenv(
    "EGRESOS_GAS_URL",
    "https://script.google.com/macros/s/AKfycbwyrAf5h-FXJ6z3MKGDlVKVTBwKDOxUoe7koeQGPWYeLlmYgb0SJIdXe22lBn3VpRzZhQ/exec",
).strip()
EGRESOS_SHEET_ID = os.getenv("EGRESOS_SHEET_ID", "").strip()
EGRESOS_SHEET_NAME = os.getenv("EGRESOS_SHEET_NAME", "Egresos diarios").strip() or "Egresos diarios"
EGRESOS_API_KEY = os.getenv("EGRESOS_API_KEY", "").strip()


def _post_gas(payload: Dict[str, Any], timeout: int | None = 20) -> Dict[str, Any]:
    if not EGRESOS_GAS_URL:
        raise RuntimeError("EGRESOS_GAS_URL no configurado")
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(EGRESOS_GAS_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if EGRESOS_API_KEY:
        req.add_header("X-API-Key", EGRESOS_API_KEY)
    try:
        with urllib.request.urlopen(req, timeout=timeout or 20) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data) if data else {"success": True}
    except urllib.error.HTTPError as e:
        err_text = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code}: {err_text}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Conexión fallida: {e}")


def _norm_fecha(fecha_str: str) -> str:
    # Acepta YYYY-MM-DD y devuelve DD/MM
    try:
        d = datetime.fromisoformat(str(fecha_str).strip()[:10])
        return d.strftime("%d/%m")
    except Exception:
        return str(fecha_str).strip()


def _map_egreso_to_row(egreso: Dict[str, Any]) -> List[Any]:
    """Mapea un egreso a la fila para la hoja 'Egresos diarios' en este orden:
    Fecha, Motivo del egreso, Costo, Responsable, Tipo, Forma de pago, Observaciones
    """
    return [
        _norm_fecha(egreso.get("fecha", "")),
        str(egreso.get("motivo", "")),
        float(egreso.get("costo", 0) or 0),
        str(egreso.get("responsable", "")),
        str(egreso.get("tipo", "")),
        str(egreso.get("pago", "")),
        str(egreso.get("observaciones", "")),
    ]


def enviar_egresos(egresos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Envía uno o varios egresos al Apps Script (appendRows)."""
    if not egresos:
        return {"success": False, "error": "NO_HAY_EGRESOS", "mensaje": "No hay egresos para enviar"}

    rows = [_map_egreso_to_row(e) for e in egresos]
    payload = {"action": "appendRows", "sheetName": EGRESOS_SHEET_NAME, "rows": rows}
    if EGRESOS_SHEET_ID:
        payload["sheetId"] = EGRESOS_SHEET_ID
    res = _post_gas(payload)
    if not res or not res.get("success", False):
        return {"success": False, "error": res.get("error") if isinstance(res, dict) else "API_ERROR", "detalle": res}
    return {"success": True, "egresos_enviados": len(rows), "detalle": res}


def estado_egresos() -> Dict[str, Any]:
    try:
        status_payload = {"action": "status", "sheetName": EGRESOS_SHEET_NAME}
        if EGRESOS_SHEET_ID:
            status_payload["sheetId"] = EGRESOS_SHEET_ID
        res = _post_gas(status_payload)
        return {"success": True, "estado": res}
    except Exception as e:
        return {"success": False, "error": str(e)}
