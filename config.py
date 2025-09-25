"""
Configuración centralizada para Milo Store ERP
"""
import os
import json

# Cargar variables de entorno desde archivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv no está instalado. Instala con: pip install python-dotenv")

def get_google_credentials():
    """Obtiene las credenciales de Google Sheets desde un archivo."""
    try:
        # Intenta cargar desde el archivo google_credentials.json
        creds_path = os.path.join(os.path.dirname(__file__), 'google_credentials.json')
        if os.path.exists(creds_path):
            with open(creds_path, 'r') as f:
                return json.load(f)
        
        # Si no encuentra el archivo, muestra un mensaje de error
        print("⚠️ No se encontró el archivo google_credentials.json")
        return {}
        
    except Exception as e:
        print(f"⚠️ Error al leer el archivo de credenciales: {e}")
        return {}

# Configuración de Google Sheets
GOOGLE_SHEETS_CONFIG = {
    "SHEET_ID": os.getenv("GOOGLE_SHEETS_SHEET_ID", "1QG8a6yHmad5sFpVcKhC3l0oEAcjJftmHV2KAF56bkkM"),
    "SHEET_NAME": os.getenv("GOOGLE_SHEETS_SHEET_NAME", "Ingreso Diario"),
    "CATALOG_GID": os.getenv("GOOGLE_SHEETS_CATALOG_GID", "180421919"),  # GID de la hoja "Códigos Stock" (catálogo)
    "TIMEOUT": int(os.getenv("GOOGLE_SHEETS_TIMEOUT", "10")),  # segundos
    "RETRY_ATTEMPTS": int(os.getenv("GOOGLE_SHEETS_RETRY_ATTEMPTS", "3")),
    "CREDENTIALS": get_google_credentials()
}

# Configuración de la aplicación
APP_CONFIG = {
    "DEBUG": True,
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "SECRET_KEY": "milo-store-secret-key-2024"
}

# Configuración de archivos
FILE_CONFIG = {
    "DATA_DIR": "data",
    "EXCEL_FILENAME": "Milo Store ERP.xlsx",  # Nombre correcto del archivo
    "BACKUP_DIR": "backups",
    "USE_EXISTING_FILE": True,  # No crear archivos nuevos
    "EXISTING_FILE_PATH": "Milo Store ERP.xlsx"  # Ruta al archivo existente
}

# Configuración de logging
LOGGING_CONFIG = {
    "LEVEL": "INFO",
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
} 