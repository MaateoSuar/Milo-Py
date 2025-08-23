"""
Configuración de desarrollo para Milo Store ERP
"""

# Configuración de desarrollo
DEBUG = True
TESTING = False

# Configuración de Google Sheets para desarrollo
GOOGLE_SHEETS_DEV = {
    "SHEET_ID": "1QG8a6yHmad5sFpVcKhC3l0oEAcjJftmHV2KAF56bkkM",
    "GID": "561161202",
    "TIMEOUT": 15,  # Más tiempo para desarrollo
    "RETRY_ATTEMPTS": 5
}

# Configuración de logging para desarrollo
LOGGING_DEV = {
    "LEVEL": "DEBUG",
    "FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "FILE": "logs/development.log"
}

# Configuración de la aplicación para desarrollo
APP_DEV = {
    "DEBUG": True,
    "HOST": "127.0.0.1",
    "PORT": 5000,
    "SECRET_KEY": "dev-secret-key-change-in-production"
} 