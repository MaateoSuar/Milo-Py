#!/usr/bin/env python3
"""
Script para probar la carga del catálogo y ver qué hojas están disponibles
"""

from services.catalog_service import CatalogService, obtener_catalogo

def test_catalogo():
    """Prueba la carga del catálogo"""
    
    print("🧪 Probando carga del catálogo...")
    
    try:
        # Crear instancia del servicio
        print("\n🔧 Creando instancia del servicio...")
        service = CatalogService()
        
        # Verificar estado del catálogo
        print("\n📊 Verificando estado del catálogo...")
        estado = service.obtener_estado_catalogo()
        print(f"Estado: {estado}")
        
        # Listar todas las hojas disponibles
        print("\n📋 Hojas disponibles en el spreadsheet:")
        for i, worksheet in enumerate(service.spreadsheet.worksheets()):
            print(f"  {i+1}. {worksheet.title} (ID: {worksheet.id})")
        
        # Intentar obtener el catálogo
        print("\n📚 Intentando obtener catálogo...")
        catalogo = obtener_catalogo()
        
        print(f"\n✅ Catálogo cargado exitosamente!")
        print(f"Total de productos: {len(catalogo)}")
        
        # Mostrar algunos ejemplos
        if catalogo:
            print("\n📝 Ejemplos de productos:")
            for i, (id_prod, nombre) in enumerate(list(catalogo.items())[:5]):
                print(f"  {i+1}. {id_prod} -> {nombre}")
        else:
            print("\n⚠️ El catálogo está vacío")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_catalogo()
