"""
Test de integración con Google Sheets

Este script prueba la conexión y escritura en Google Sheets usando las credenciales configuradas.
"""
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Asegurarse de que el directorio raíz esté en el path
sys.path.append(str(Path(__file__).parent.absolute()))

# Cargar variables de entorno
load_dotenv()

def test_google_sheets_connection():
    """Prueba la conexión con Google Sheets y la escritura básica."""
    try:
        print("\n=== Iniciando prueba de conexión con Google Sheets ===")
        
        # Importar aquí para capturar mejor los errores de importación
        from services.google_sheets_writer import GoogleSheetsWriter
        
        print("\n🔧 Inicializando GoogleSheetsWriter...")
        sheets_writer = GoogleSheetsWriter()
        
        # Obtener información de la hoja
        print("\n📊 Obteniendo información de la hoja...")
        estado = sheets_writer.obtener_estado_sheets()
        print("\n📝 Estado actual de la hoja:")
        for key, value in estado.items():
            print(f"   {key}: {value}")
        
        # Prueba de escritura
        print("\n✏️  Probando escritura...")
        fila_prueba = ["Prueba", "Esta es una fila de prueba", "TEST123", "Producto de prueba", 
                      "10000", "1", "10000", "5000", "Prueba", "Efectivo", "10000", "50%"]
        
        # Escribir en la siguiente fila disponible
        ultima_fila = sheets_writer.obtener_ultima_fila_confiable()
        fila_destino = ultima_fila + 1
        
        print(f"   Escribiendo en fila {fila_destino}...")
        sheets_writer.worksheet.update(f"A{fila_destino}", [fila_prueba])
        print(f"✅ Prueba de escritura exitosa en fila {fila_destino}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Iniciando pruebas de integración con Google Sheets ===\n")
    
    # Verificar si las credenciales están configuradas
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if not creds_json and not os.path.exists("google_credentials.json"):
        print("""
❌ No se encontraron credenciales de Google Sheets.
   Por favor, configura una de las siguientes opciones:
   1. Variable de entorno GOOGLE_CREDENTIALS_JSON con el contenido del JSON de credenciales
   2. Archivo google_credentials.json en el directorio raíz del proyecto
   
   Asegúrate de que las credenciales tengan el formato correcto y los permisos necesarios.
   Para más información, revisa la documentación de Google Cloud Platform.
   """)
        sys.exit(1)
    
    # Ejecutar la prueba
    if test_google_sheets_connection():
        print("\n✅ ¡Prueba completada exitosamente!")
    else:
        print("\n❌ La prueba encontró algunos problemas. Por favor, revisa los mensajes de error.")
        sys.exit(1)
