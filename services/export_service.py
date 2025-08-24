import os
from pathlib import Path
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from .sales_service import listar_ventas
from config import FILE_CONFIG, GOOGLE_SHEETS_CONFIG

# Usar la configuración del archivo
DATA_DIR = Path(FILE_CONFIG["DATA_DIR"])
EXCEL_FILE = Path(FILE_CONFIG["EXCEL_FILENAME"])  # Archivo existente del usuario
BACKUP_DIR = Path(FILE_CONFIG["BACKUP_DIR"])

# Orden y nombres de columnas según la estructura de Google Sheets
COLUMNS = [
    "Fecha",
    "Notas",
    "Id",
    "Nombre del Elemento",
    "Precio",
    "Unidades",
    "Precio Unitario",
    "Costo U",
    "Tipo"
]

def _ventas_a_dataframe(ventas: list[dict]) -> pd.DataFrame:
    rows = []
    for v in ventas:
        rows.append({
            "Fecha": v.get("fecha", ""),
            "Notas": v.get("notas", ""),
            "Id": v.get("id", ""),
            "Nombre del Elemento": v.get("nombre", ""),
            "Precio": v.get("precio", ""),
            "Unidades": v.get("unidades", ""),
            "Precio Unitario": v.get("precio", ""),
            "Costo U": "",  # Dejar vacío o calcular si es necesario
            "Tipo": ""  # Dejar vacío o establecer un valor por defecto
        })
    df = pd.DataFrame(rows, columns=COLUMNS)
    return df

def exportar_excel(path: Path = EXCEL_FILE) -> Path:
    """
    Exporta las ventas al archivo Excel existente del usuario
    """
    ventas = listar_ventas()
    
    # Verificar si existe el archivo original del usuario
    if not path.exists():
        # Si no existe, crear directorio y archivo con encabezados
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            pd.DataFrame(columns=COLUMNS).to_excel(path, index=False)
            print(f"✅ Archivo Excel creado: {path}")
        return path
    
    try:
        # Leer el archivo existente del usuario
        print(f"📖 Leyendo archivo existente: {path}")
        df_existente = pd.read_excel(path)
        print(f"   Filas existentes: {len(df_existente)}")
        
        # Preparar nuevas ventas
        if ventas:
            df_nuevas = _ventas_a_dataframe(ventas)
            print(f"   Nuevas ventas: {len(df_nuevas)}")
            
            # Combinar datos existentes con nuevos
            df_final = pd.concat([df_existente, df_nuevas], ignore_index=True)
            print(f"   Total final: {len(df_final)} filas")
        else:
            df_final = df_existente
            print("   No hay nuevas ventas para agregar")
        
        # Crear backup antes de sobrescribir
        BACKUP_DIR.mkdir(exist_ok=True)
        backup_file = BACKUP_DIR / f"backup_{path.stem}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df_existente.to_excel(backup_file, index=False)
        print(f"💾 Backup creado: {backup_file}")
        
        # Escribir al archivo original del usuario
        df_final.to_excel(path, index=False, engine="openpyxl")
        print(f"✅ Ventas exportadas al archivo: {path}")
        
        return path
        
    except Exception as e:
        print(f"❌ Error exportando a Excel: {e}")
        # En caso de error, crear archivo nuevo
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if ventas:
            df_new = _ventas_a_dataframe(ventas)
            df_new.to_excel(path, index=False, engine="openpyxl")
            print(f"✅ Archivo Excel recreado: {path}")
        return path

def exportar_a_google_sheets(ventas: list[dict] = None) -> dict:
    """
    Exporta las ventas a Google Sheets de manera optimizada.
    """
    if ventas is None:
        ventas = listar_ventas()
    
    if not ventas:
        return {"success": True, "message": "No hay datos para exportar"}
        
    try:
        # Autenticación
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            GOOGLE_SHEETS_CONFIG["CREDENTIALS"], 
            scope
        )
        client = gspread.authorize(creds)
        
        # Abrir la hoja de cálculo
        sheet = client.open_by_key(GOOGLE_SHEETS_CONFIG["SHEET_ID"])
        
        # Intentar obtener la hoja activa o crear una nueva
        try:
            worksheet = sheet.worksheet(GOOGLE_SHEETS_CONFIG["SHEET_NAME"])
        except gspread.WorksheetNotFound:
            # Si no existe la hoja, crearla con un tamaño inicial más grande
            worksheet = sheet.add_worksheet(
                title=GOOGLE_SHEETS_CONFIG["SHEET_NAME"], 
                rows=1000, 
                cols=len(COLUMNS)
            )
            # Agregar encabezados
            worksheet.append_row(COLUMNS)
            next_row = 2  # Empezar desde la fila 2 (después de los encabezados)
        else:
            # Usar col_values que es más rápido que get_all_values()
            col_a = worksheet.col_values(1)
            next_row = len(col_a) + 1 if col_a else 1
            
            # Si la hoja está vacía, agregar encabezados
            if next_row == 1:
                worksheet.append_row(COLUMNS)
                next_row = 2
        
        # Preparar datos para exportar en un solo lote
        batch_data = []
        for venta in ventas:
            batch_data.append([
                venta.get("fecha", ""),  # Fecha
                venta.get("notas", ""),   # Notas
                venta.get("id", ""),       # Id
                venta.get("nombre", ""),   # Nombre del Elemento
                venta.get("precio", ""),   # Precio
                venta.get("unidades", ""), # Unidades
                venta.get("precio", ""),   # Precio Unitario
                "",                        # Costo U (vacío)
                ""                         # Tipo (vacío)
            ])
        
        # Escribir todos los datos en un solo lote
        if batch_data:
            # Calcular el rango de destino
            end_row = next_row + len(batch_data) - 1
            range_name = f"A{next_row}:I{end_row}"
            
            # Usar actualización por lotes para mejor rendimiento
            worksheet.update(range_name, batch_data, value_input_option='USER_ENTERED')
        
        return {
            "success": True,
            "message": "Exportado con éxito",
            "url": f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_CONFIG['SHEET_ID']}/edit#gid={worksheet.id}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al exportar a Google Sheets: {str(e)}"
        }
