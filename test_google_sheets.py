from services.google_sheets_writer import GoogleSheetsWriter

def test_conexion():
    try:
        print("Probando conexion con Google Sheets...")
        sheets_writer = GoogleSheetsWriter()
        estado = sheets_writer.obtener_estado_sheets()
        
        if estado["success"]:
            print("✅ Conexion exitosa con Google Sheets")
            print(f"URL: {estado['url']}")
            print(f"Hoja: {estado['nombre_hoja']}")
            print(f"Total de filas: {estado['total_filas']}")
            print("\nPrimeras filas de ejemplo:")
            for i, fila in enumerate(estado['ejemplo_datos'][:5], 1):
                print(f"Fila {i}: {fila}")
        else:
            print(f"❌ Error al conectar con Google Sheets: {estado.get('error', 'Error desconocido')}")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

if __name__ == "__main__":
    test_conexion()
