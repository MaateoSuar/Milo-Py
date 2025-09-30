import os
import time
import random
from pathlib import Path
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
{{ ... }}
            "url": f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_CONFIG['SHEET_ID']}/edit#gid={worksheet.id}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al exportar a Google Sheets: {str(e)}"
        }

def exportar_ventas_seguro_google_sheets(
    ventas: list[dict] = None,
    sheet_name: str | None = None,
    limpiar_antes: bool = True,
    chunk_size: int = 10**9,
) -> dict:
    """
    Exporta TODAS las Ventas en UNA sola actualización por rango.
    - Minimiza cuota (una llamada grande)
    - Re intentos con backoff ante 409/429
    - Usa hoja fija (por defecto 'Export Ventas' o env GOOGLE_SHEETS_EXPORT_SHEET_NAME)
    """
    try:
        if not ventas:
            try:
                from .sales_service import listar_ventas  # type: ignore
                ventas = listar_ventas()
            except Exception:
                pass

        if not Ventas:
            return {"success": True, "message": "No hay datos para exportar"}

        target_sheet_name = (
            sheet_name
            or os.getenv("GOOGLE_SHEETS_EXPORT_SHEET_NAME")
            or "Export Ventas"
        )

        # Autenticación con normalización de private_key
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(GOOGLE_SHEETS_CONFIG.get("CREDENTIALS") or {})
        if isinstance(creds_dict.get("private_key"), str):
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # Abrir spreadsheet/hoja
        sheet = client.open_by_key(GOOGLE_SHEETS_CONFIG["SHEET_ID"])
        try:
            worksheet = sheet.worksheet(target_sheet_name)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(
                title=target_sheet_name,
                rows=max(1000, len(Ventas) + 10),
                cols=len(COLUMNS),
            )

        # Encabezados A1:I1
        try:
            header_values = worksheet.row_values(1)
        except Exception:
            header_values = []
        if not header_values:
            worksheet.update("A1:I1", [COLUMNS], value_input_option='USER_ENTERED')

        # Preparar filas A..I
        batch_data = []
        for v in Ventas:
            batch_data.append([
                v.get("fecha", ""),
                v.get("notas", ""),
                v.get("id", ""),
                v.get("nombre", ""),
                v.get("precio", ""),
                v.get("unidades", ""),
                v.get("precio", ""),
                "",
                "",
            ])

        total_rows_needed = 1 + max(1, len(batch_data))
        if worksheet.row_count < total_rows_needed:
            try:
                worksheet.resize(rows=total_rows_needed, cols=max(worksheet.col_count, len(COLUMNS)))
            except Exception:
                pass

        if limpiar_antes:
            try:
                worksheet.batch_clear(["A2:I"])
            except Exception:
                pass

        # ÚNICA llamada (o mínima) con backoff anti-409/429
        start_row = 2
        written = 0
        while written < len(batch_data):
            chunk = batch_data[written: written + chunk_size]
            end_row = start_row + len(chunk) - 1
            rng = f"A{start_row}:I{end_row}"
            max_attempts = 5
            base_sleep = 0.5
            for attempt in range(max_attempts):
                try:
                    worksheet.update(rng, chunk, value_input_option='USER_ENTERED')
                    break
                except gspread.exceptions.APIError as e:
                    msg = str(e).lower()
                    transient = (
                        '409' in msg or 'quota' in msg or 'rate' in msg or 'exceeded' in msg or 'backend' in msg or 'internal error' in msg
                    )
                    if transient and attempt < max_attempts - 1:
                        delay = base_sleep * (2 ** attempt) + random.uniform(0, 0.25)
                        time.sleep(delay)
                        continue
                    raise
            written += len(chunk)
            start_row = end_row + 1

        return {
            "success": True,
            "message": f"Exportado con éxito a hoja '{target_sheet_name}'",
            "url": f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_CONFIG['SHEET_ID']}/edit#gid={ worksheet.id}",
            "filas": len(batch_data),
            "hoja": target_sheet_name,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al exportar a Google Sheets (seguro): {str(e)}",
        }
