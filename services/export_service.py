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
    Exporta las ventas a Google Sheets, manejando automáticamente la creación de nuevas hojas
    cuando se alcance el límite de filas.
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
            # Si no existe la hoja, crearla
            worksheet = sheet.add_worksheet(
                title=GOOGLE_SHEETS_CONFIG["SHEET_NAME"], 
                rows=1000, 
                cols=len(COLUMNS)
            )
            # Agregar encabezados
            worksheet.append_row(COLUMNS)
            last_row = 1
            return _escribir_datos(worksheet, ventas, last_row)
        
        # Obtener todas las filas y encontrar la última con datos
        all_values = worksheet.get_all_values()
        
        # Encontrar la última fila con datos reales
        last_non_empty_row = 0
        for i, row in enumerate(all_values, 1):
            if any(cell.strip() for cell in row):
                last_non_empty_row = i
        
        # La siguiente fila disponible es después de la última con datos
        next_row = last_non_empty_row + 1
        
        # Si la hoja está vacía, agregar encabezados
        if last_non_empty_row == 0:
            worksheet.append_row(COLUMNS)
            next_row = 2  # Empezar a escribir desde la fila 2
        
        # Verificar si hay suficiente espacio
        max_rows = 1000  # Un límite razonable para empezar
        if next_row + len(ventas) - 1 > max_rows:
            # Buscar filas vacías para reutilizar
            empty_rows = []
            for i, row in enumerate(all_values, 1):
                if i > last_non_empty_row:
                    break
                if not any(cell.strip() for cell in row):
                    empty_rows.append(i)
            
            # Si hay suficientes filas vacías, usarlas
            if len(empty_rows) >= len(ventas):
                next_row = empty_rows[0]
            else:
                return {
                    "success": False,
                    "message": f"No hay suficiente espacio en la hoja. Por favor, limpia filas vacías o crea una nueva hoja."
                }
        
        # Preparar datos para exportar
        datos = []
        for venta in ventas:
            datos.append([
                venta.get("fecha", ""),  # Fecha
                venta.get("notas", ""),   # Notas
                venta.get("id", ""),       # Id
                venta.get("nombre", ""),   # Nombre del Elemento
                venta.get("precio", ""),   # Precio
                venta.get("unidades", ""), # Unidades
                venta.get("precio", ""),   # Precio Unitario (mismo que Precio)
                "",                        # Costo U (vacío)
                ""                         # Tipo (vacío)
            ])
        
        # Escribir los datos en la siguiente fila disponible
        if datos:
            # Usar range para especificar exactamente dónde escribir (A a I para 9 columnas)
            range_name = f"A{next_row}:I{next_row + len(datos) - 1}"
            worksheet.update(range_name, datos, value_input_option='USER_ENTERED')
        
        return {
            "success": True,
            "message": f"Se exportaron {len(ventas)} ventas correctamente (fila {next_row} a {next_row + len(datos) - 1})",
            "url": f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEETS_CONFIG['SHEET_ID']}/edit#gid={worksheet.id}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al exportar a Google Sheets: {str(e)}"
        }
