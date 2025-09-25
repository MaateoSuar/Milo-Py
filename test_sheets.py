from services.google_sheets_writer import GoogleSheetsWriter

if __name__ == "__main__":
    try:
        writer = GoogleSheetsWriter()
        print("✅ Conexión a Google Sheets exitosa")
        try:
            sheets = [ws.title for ws in writer.spreadsheet.worksheets()]
            print("Hojas disponibles:", sheets)
        except Exception as e:
            print("⚠️ Conectó pero no se pudieron listar hojas:", e)
    except Exception as e:
        print("❌ Error al conectar a Google Sheets:", e)


