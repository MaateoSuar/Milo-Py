"""
Prueba simple de conexión a Google Sheets
"""
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("=== Iniciando prueba simple de Google Sheets ===\n")

# Verificar credenciales
creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not creds_json and not os.path.exists("google_credentials.json"):
    print("❌ No se encontraron credenciales de Google Sheets")
    print("   Configura la variable de entorno GOOGLE_CREDENTIALS_JSON o el archivo google_credentials.json")
    sys.exit(1)

# Importar después de verificar credenciales
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    import json
    
    # Cargar credenciales
    if creds_json:
        creds_dict = json.loads(creds_json)
        print("✅ Credenciales cargadas desde variable de entorno")
    else:
        with open("google_credentials.json", "r") as f:
            creds_dict = json.load(f)
        print("✅ Credenciales cargadas desde archivo")
    
    # Configurar alcances
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Crear credenciales
    print("\n🔑 Creando credenciales...")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    print(f"✅ Credenciales creadas para: {creds.service_account_email}")
    
    # Autenticar
    print("\n🔌 Autenticando con Google Sheets...")
    client = gspread.authorize(creds)
    print("✅ Autenticación exitosa")
    
    # Intentar abrir una hoja de prueba
    print("\n📊 Listando las primeras 5 hojas de cálculo disponibles:")
    try:
        spreadsheets = client.openall()[:5]  # Limitar a 5 para no sobrecargar
        for i, sheet in enumerate(spreadsheets, 1):
            print(f"   {i}. {sheet.title} (ID: {sheet.id})")
        print("\n✅ Prueba completada exitosamente")
    except Exception as e:
        print(f"❌ Error al listar hojas: {str(e)}")
    
except ImportError as e:
    print(f"❌ Error de importación: {str(e)}")
    print("   Asegúrate de instalar las dependencias con: pip install gspread oauth2client")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error durante la prueba: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
