#!/usr/bin/env python3
"""
Script de prueba para verificar que los campos del formulario se estén enviando correctamente
"""

import json
from services.sales_service import agregar_venta, listar_ventas
from services.google_sheets_writer import GoogleSheetsWriter

def test_campos_formulario():
    """Prueba que los campos se envíen correctamente"""
    
    print("🧪 Probando campos del formulario...")
    
    # Datos de prueba
    venta_prueba = {
        "fecha": "2024-01-15",
        "id": "TEST001",
        "nombre": "Producto de Prueba",
        "precio": 25.50,
        "unidades": 3,
        "pago": "Credito",
        "notas": "Prueba de campos"
    }
    
    print(f"📝 Datos de prueba: {json.dumps(venta_prueba, indent=2)}")
    
    try:
        # Agregar venta
        print("\n➕ Agregando venta...")
        agregar_venta(venta_prueba)
        print("✅ Venta agregada exitosamente")
        
        # Verificar que se agregó en memoria
        ventas = listar_ventas()
        print(f"📊 Total de ventas en memoria: {len(ventas)}")
        
        if ventas:
            ultima_venta = ventas[-1]
            print(f"🔄 Última venta en memoria: {json.dumps(ultima_venta, indent=2)}")
            
            # Verificar campos específicos
            print("\n🔍 Verificando campos específicos:")
            print(f"   Precio: {ultima_venta.get('precio')} (tipo: {type(ultima_venta.get('precio'))})")
            print(f"   Unidades: {ultima_venta.get('unidades')} (tipo: {type(ultima_venta.get('unidades'))})")
            print(f"   Forma de Pago: {ultima_venta.get('pago')} (tipo: {type(ultima_venta.get('pago'))})")
        
        # Probar Google Sheets directamente
        print("\n🌐 Probando Google Sheets directamente...")
        sheets_writer = GoogleSheetsWriter()
        
        # Preparar fila
        fila_datos = sheets_writer.preparar_fila_venta(venta_prueba)
        print(f"📋 Fila preparada: {fila_datos}")
        
        # Verificar campos específicos en la fila
        print("\n🔍 Verificando campos en la fila preparada:")
        print(f"   Columna E (Precio): '{fila_datos[4]}'")
        print(f"   Columna F (Unidades): '{fila_datos[5]}'")
        print(f"   Columna J (Forma de Pago): '{fila_datos[9]}'")
        
        # Verificar que no estén vacíos
        if fila_datos[4] and fila_datos[4] != "":
            print("✅ Campo Precio: OK")
        else:
            print("❌ Campo Precio: VACÍO")
            
        if fila_datos[5] and fila_datos[5] != "":
            print("✅ Campo Unidades: OK")
        else:
            print("❌ Campo Unidades: VACÍO")
            
        if fila_datos[9] and fila_datos[9] != "":
            print("✅ Campo Forma de Pago: OK")
        else:
            print("❌ Campo Forma de Pago: VACÍO")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_campos_formulario()
