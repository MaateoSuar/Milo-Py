#!/usr/bin/env python3
"""
Script de demostración para Milo Store ERP
"""

import sys
import os
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def mostrar_banner():
    print("=" * 60)
    print("🏪 MILO STORE ERP - DEMOSTRACIÓN")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)

def probar_catalogo():
    print("\n🔄 Probando conexión con Google Sheets...")
    try:
        from services.catalog_service import obtener_catalogo
        catalogo = obtener_catalogo()
        print(f"✅ Catálogo conectado: {len(catalogo)} productos disponibles")
        return True
    except Exception as e:
        print(f"❌ Error en catálogo: {e}")
        return False

def probar_ventas():
    print("\n🔄 Probando servicio de ventas...")
    try:
        from services.sales_service import agregar_venta, listar_ventas
        from datetime import datetime
        
        # Agregar una venta de prueba
        venta_prueba = {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "id": "A1",
            "nombre": "Aritos Rango de precio 1",
            "precio": 25.50,
            "unidades": 2,
            "pago": "Efectivo",
            "notas": "Venta de prueba"
        }
        
        agregar_venta(venta_prueba)
        ventas = listar_ventas()
        print(f"✅ Servicio de ventas funcionando: {len(ventas)} ventas registradas")
        return True
    except Exception as e:
        print(f"❌ Error en ventas: {e}")
        return False

def probar_exportacion():
    print("\n🔄 Probando servicio de exportación...")
    try:
        from services.export_service import exportar_excel
        from pathlib import Path
        
        archivo = exportar_excel()
        if archivo.exists():
            print(f"✅ Exportación funcionando: {archivo}")
            return True
        else:
            print("❌ Archivo no generado")
            return False
    except Exception as e:
        print(f"❌ Error en exportación: {e}")
        return False

def main():
    mostrar_banner()
    
    print("\n🚀 Iniciando pruebas de funcionalidad...")
    
    # Probar catálogo
    catalogo_ok = probar_catalogo()
    
    # Probar ventas
    ventas_ok = probar_ventas()
    
    # Probar exportación
    exportacion_ok = probar_exportacion()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"🔗 Catálogo (Google Sheets): {'✅ OK' if catalogo_ok else '❌ ERROR'}")
    print(f"💰 Servicio de Ventas: {'✅ OK' if ventas_ok else '❌ ERROR'}")
    print(f"📤 Exportación a Excel: {'✅ OK' if exportacion_ok else '❌ ERROR'}")
    
    if all([catalogo_ok, ventas_ok, exportacion_ok]):
        print("\n🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("🚀 La aplicación está lista para usar")
        print("\n💡 Para ejecutar la aplicación web:")
        print("   py app.py")
        print("   Luego abre: http://localhost:5000")
    else:
        print("\n⚠️  Algunas pruebas fallaron")
        print("🔧 Revisa los errores arriba")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 