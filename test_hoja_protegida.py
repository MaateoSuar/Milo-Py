#!/usr/bin/env python3
"""
Script para probar la detección de protección de hoja y escribir solo en columnas libres
"""

from services.google_sheets_writer import GoogleSheetsWriter

def test_hoja_protegida():
    """Prueba la detección de protección y escritura en columnas libres"""
    
    print("🧪 Probando hoja protegida...")
    
    try:
        # Inicializar el escritor
        sheets_writer = GoogleSheetsWriter()
        
        # Verificar si la hoja está protegida
        print("\n🔒 Verificando protección de hoja...")
        hoja_protegida = sheets_writer._verificar_si_hoja_protegida()
        print(f"Hoja protegida: {hoja_protegida}")
        
        # Obtener estado de la hoja
        print("\n📊 Obteniendo estado de la hoja...")
        estado = sheets_writer.obtener_estado_sheets()
        print(f"Estado: {estado}")
        
        # Intentar escribir una fila de prueba
        print("\n✍️ Intentando escribir fila de prueba...")
        
        # Datos de prueba
        venta_prueba = {
            "fecha": "2024-01-15",
            "id": "TEST002",
            "nombre": "Producto Test 2",
            "precio": 15.75,
            "unidades": 2,
            "pago": "Debito",
            "notas": "Prueba hoja protegida"
        }
        
        # Preparar fila
        fila_datos = sheets_writer.preparar_fila_venta(venta_prueba)
        print(f"Fila preparada: {fila_datos}")
        
        # Obtener próxima fila
        proxima_fila = sheets_writer.obtener_ultima_fila_confiable()
        print(f"Próxima fila disponible: {proxima_fila}")
        
        # Intentar escribir usando el método para hojas protegidas
        print(f"\n🔄 Intentando escribir en fila {proxima_fila} (método para hojas protegidas)...")
        
        resultado = sheets_writer.escribir_fila_sin_expandir(fila_datos, proxima_fila)
        
        if resultado:
            print("✅ Escritura exitosa usando método para hojas protegidas")
        else:
            print("❌ Falló la escritura usando método para hojas protegidas")
            
        # Verificar qué se escribió realmente
        print(f"\n🔍 Verificando qué se escribió en la fila {proxima_fila}...")
        try:
            # Leer la fila escrita
            fila_escrita = sheets_writer.worksheet.row_values(proxima_fila)
            print(f"Fila leída: {fila_escrita}")
            
            # Verificar campos específicos
            if len(fila_escrita) >= 10:
                print(f"Columna E (Precio): '{fila_escrita[4]}'")
                print(f"Columna F (Unidades): '{fila_escrita[5]}'")
                print(f"Columna J (Forma de Pago): '{fila_escrita[9]}'")
            else:
                print(f"La fila solo tiene {len(fila_escrita)} columnas")
                
        except Exception as e:
            print(f"Error leyendo la fila: {e}")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hoja_protegida()
