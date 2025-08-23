import os
from pathlib import Path
import pandas as pd
from .sales_service import listar_ventas
from config import FILE_CONFIG

# Usar la configuración del archivo
DATA_DIR = Path(FILE_CONFIG["DATA_DIR"])
EXCEL_FILE = Path(FILE_CONFIG["EXCEL_FILENAME"])  # Archivo existente del usuario
BACKUP_DIR = Path(FILE_CONFIG["BACKUP_DIR"])

# Orden y nombres de columnas como tu export original
COLUMNS = [
    "Fecha",
    "ID Producto",
    "Nombre del Producto",
    "Precio Unitario",
    "Unidades",
    "Total",
    "Forma de Pago",
    "Notas"
]

def _ventas_a_dataframe(ventas: list[dict]) -> pd.DataFrame:
    rows = []
    for v in ventas:
        rows.append({
            "Fecha": v["fecha"],
            "ID Producto": v["id"],
            "Nombre del Producto": v["nombre"],
            "Precio Unitario": v["precio"],
            "Unidades": v["unidades"],
            "Total": v["total"],
            "Forma de Pago": v["pago"],
            "Notas": v["notas"]
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
