import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint

# Configuración
SHEET_ID = "1_-YxmdfqUVMFcRQFBy6bYWJXK0dmPhMft1z_O0PeieU"
SHEET_NAME = "Ingreso Diario"

# Configurar el alcance
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/drive"]

# Autenticación
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Abrir la hoja de cálculo
print(f"Abriendo la hoja de cálculo con ID: {SHEET_ID}")
try:
    sheet = client.open_by_key(SHEET_ID)
    print(f"Hoja de cálculo abierta: {sheet.title}")
    
    # Listar todas las hojas
    print("\nHojas disponibles:")
    for i, worksheet in enumerate(sheet.worksheets(), 1):
        print(f"{i}. {worksheet.title} (ID: {worksheet.id})")
    
    # Intentar abrir la hoja por nombre
    try:
        worksheet = sheet.worksheet(SHEET_NAME)
        print(f"\nHoja '{SHEET_NAME}' encontrada")
        
        # Leer algunas filas
        records = worksheet.get_all_records()
        print(f"\nTotal de registros: {len(records)}")
        
        if records:
            print("\nPrimer registro:")
            pprint(records[0])
        else:
            print("No se encontraron registros en la hoja")
            
    except Exception as e:
        print(f"\nError al abrir la hoja '{SHEET_NAME}': {str(e)}")
        print("Intentando con la primera hoja...")
        
        # Intentar con la primera hoja
        worksheet = sheet.get_worksheet(0)
        print(f"\nUsando la primera hoja: {worksheet.title}")
        
        # Leer algunas filas
        records = worksheet.get_all_records()
        print(f"\nTotal de registros: {len(records)}")
        
        if records:
            print("\nPrimer registro:")
            pprint(records[0])
        else:
            print("No se encontraron registros en la hoja")
    
except Exception as e:
    print(f"Error al abrir la hoja de cálculo: {str(e)}")
