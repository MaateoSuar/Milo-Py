"""
Configuración centralizada para Milo Store ERP
"""

# Configuración de Google Sheets
GOOGLE_SHEETS_CONFIG = {
    "SHEET_ID": "1QG8a6yHmad5sFpVcKhC3l0oEAcjJftmHV2KAF56bkkM",
    "GID": "561161202",
    "TIMEOUT": 10,  # segundos
    "RETRY_ATTEMPTS": 3
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