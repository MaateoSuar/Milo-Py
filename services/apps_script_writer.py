"""
Writer basado en Google Apps Script (GAS) para exportar ventas sin usar la API de Sheets.
Envía las ventas vía HTTP POST a un Web App publicado en Apps Script.
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
import csv
import urllib.request
import urllib.error

from config import GOOGLE_APPS_SCRIPT

logger = logging.getLogger(__name__)


class AppsScriptWriter:
    def __init__(self):
        self.gas_url = (GOOGLE_APPS_SCRIPT.get("GAS_URL") or "").strip()
        self.api_key = (GOOGLE_APPS_SCRIPT.get("GAS_API_KEY") or "").strip()
        if not self.gas_url:
            raise ValueError("GAS_URL no configurado. Define la URL del Web App de Apps Script")

        # Directorio de datos locales (para backup CSV)
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # Headers esperados (A..L)
        self.expected_headers = [
            "Fecha", "Notas", "ID", "Nombre del Elemento", "Precio",
            "Unidades", "Precio Unitario", "Costo U", "Tipo",
            "Forma de Pago", "Costo Total", "Margen"
        ]

    def normalizar_fila_datos(self, fila_datos):
        while len(fila_datos) < len(self.expected_headers):
            fila_datos.append("")
        if len(fila_datos) > len(self.expected_headers):
            fila_datos = fila_datos[:len(self.expected_headers)]
        return fila_datos

    def preparar_fila_venta(self, venta: dict):
        # precio ingresado es unitario
        precio_unitario = round(float(venta["precio"]), 2)
        unidades = int(venta["unidades"])  # asegurar entero
        precio_total = round(precio_unitario * unidades, 2)
        margen = precio_total

        fecha_obj = datetime.fromisoformat(str(venta["fecha"]))
        fila = [
            fecha_obj.strftime("%d/%m"),            # A: Fecha
            str(venta.get("notas", "")),          # B: Notas
            str(venta["id"]).upper(),              # C: ID
            str(venta["nombre"]),                  # D: Nombre
            float(precio_total),                     # E: Precio (total)
            int(unidades),                           # F: Unidades
            float(precio_unitario),                  # G: Precio Unitario
            "Sin stock",                            # H: Costo U (placeholder)
            "",                                     # I: Tipo
            str(venta.get("pago", "Otro")),       # J: Forma de pago
            float(precio_total),                     # K: Costo Total
            float(margen)                            # L: Margen
        ]
        return self.normalizar_fila_datos(fila)

    def _post_gas(self, payload: dict, timeout: int = None):
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.gas_url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("X-API-Key", self.api_key)
        try:
            with urllib.request.urlopen(req, timeout=timeout or GOOGLE_APPS_SCRIPT.get("TIMEOUT", 15)) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data) if data else {"success": True}
        except urllib.error.HTTPError as e:
            err_text = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {e.code}: {err_text}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Conexión fallida: {e}")

    def obtener_estado_gas(self):
        try:
            res = self._post_gas({"action": "status"})
            return {"success": True, "gas": res}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def agregar_multiples_ventas_a_sheets(self, ventas: list):
        if not ventas:
            return {"success": False, "error": "NO_HAY_VENTAS", "mensaje": "No hay ventas para exportar"}

        # Preparar filas
        filas = [self.preparar_fila_venta(v) for v in ventas]

        # Backup CSV local
        try:
            csv_file = self.data_dir / "ventas_para_sheets.csv"
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for fila in filas:
                    writer.writerow(fila)
        except Exception as e:
            logger.warning(f"No se pudo escribir CSV local: {e}")

        # Enviar en uno o varios lotes si necesario
        max_batch = 300  # prudente; Apps Script puede procesar cientos por llamada
        total = 0
        errores = []
        for i in range(0, len(filas), max_batch):
            lote = filas[i:i+max_batch]
            payload = {
                "action": "appendRows",
                "rows": lote
            }
            try:
                res = self._post_gas(payload)
                if not res or not res.get("success", False):
                    errores.append(res)
                else:
                    total += len(lote)
            except Exception as e:
                errores.append(str(e))

        if total == len(filas):
            return {"success": True, "ventas_exportadas": total, "mensaje": f"✅ {total} ventas exportadas vía Apps Script"}
        else:
            return {
                "success": False,
                "error": "EXPORT_PARTIAL",
                "ventas_exportadas": total,
                "errores": errores,
                "mensaje": f"⚠️ {total}/{len(filas)} ventas exportadas vía Apps Script"
            }


