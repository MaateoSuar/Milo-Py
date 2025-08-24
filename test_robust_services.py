"""
Prueba de los servicios robustos mejorados
"""
import logging
from services.google_sheets_writer import GoogleSheetsWriter
from services.catalog_service import CatalogService

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_catalog_service():
    """Prueba el servicio de catálogo robusto"""
    print("\n" + "="*50)
    print("PRUEBA DEL SERVICIO DE CATÁLOGO ROBUSTO")
    print("="*50)
    
    try:
        # Crear instancia del servicio
        catalog_service = CatalogService()
        print("✅ CatalogService inicializado correctamente")
        
        # Obtener estado del catálogo
        estado = catalog_service.obtener_estado_catalogo()
        if estado["success"]:
            print(f"✅ Estado del catálogo: {estado}")
        else:
            print(f"❌ Error obteniendo estado: {estado}")
            return
        
        # Obtener catálogo
        catalogo = catalog_service.obtener_catalogo()
        print(f"✅ Catálogo obtenido: {len(catalogo)} productos")
        
        # Mostrar algunos ejemplos
        if catalogo:
            print("\nEjemplos de productos:")
            for i, (id_prod, nombre) in enumerate(list(catalogo.items())[:5]):
                print(f"  {i+1}. {id_prod} -> {nombre}")
        
    except Exception as e:
        print(f"❌ Error en test_catalog_service: {e}")
        logger.error(f"Error en test_catalog_service: {e}")

def test_google_sheets_writer():
    """Prueba el servicio de escritura robusto"""
    print("\n" + "="*50)
    print("PRUEBA DEL SERVICIO DE ESCRITURA ROBUSTO")
    print("="*50)
    
    try:
        # Crear instancia del servicio
        writer = GoogleSheetsWriter()
        print("✅ GoogleSheetsWriter inicializado correctamente")
        
        # Obtener estado de la hoja
        estado = writer.obtener_estado_sheets()
        if estado["success"]:
            print(f"✅ Estado de la hoja: {estado}")
        else:
            print(f"❌ Error obteniendo estado: {estado}")
            return
        
        # Probar detección de última fila confiable
        ultima_fila = writer.obtener_ultima_fila_confiable()
        print(f"✅ Última fila confiable: {ultima_fila}")
        
        # Probar normalización de fila
        fila_ejemplo = ["01/01", "Test", "TEST001", "Producto Test"]
        fila_normalizada = writer.normalizar_fila_datos(fila_ejemplo)
        print(f"✅ Fila normalizada: {fila_normalizada}")
        print(f"   Longitud: {len(fila_normalizada)} (esperado: {len(writer.expected_headers)})")
        
        # Probar preparación de venta
        venta_ejemplo = {
            "fecha": "2024-01-01",
            "notas": "Venta de prueba",
            "id": "TEST001",
            "nombre": "Producto de Prueba",
            "precio": 100.50,
            "unidades": 2,
            "pago": "Efectivo"
        }
        
        fila_venta = writer.preparar_fila_venta(venta_ejemplo)
        print(f"✅ Fila de venta preparada: {fila_venta}")
        
    except Exception as e:
        print(f"❌ Error en test_google_sheets_writer: {e}")
        logger.error(f"Error en test_google_sheets_writer: {e}")

def test_error_handling():
    """Prueba el manejo robusto de errores"""
    print("\n" + "="*50)
    print("PRUEBA DEL MANEJO ROBUSTO DE ERRORES")
    print("="*50)
    
    try:
        # Probar con credenciales inválidas (simular error de permisos)
        print("⚠️  Nota: Esta prueba requiere credenciales válidas para funcionar completamente")
        
        # Crear instancia del servicio
        writer = GoogleSheetsWriter()
        
        # Simular una venta que podría causar errores
        venta_test = {
            "fecha": "2024-01-01",
            "notas": "Test de manejo de errores",
            "id": "ERROR001",
            "nombre": "Producto Test Error",
            "precio": 50.00,
            "unidades": 1,
            "pago": "Tarjeta"
        }
        
        # Intentar agregar la venta (esto podría fallar si no hay permisos)
        resultado = writer.agregar_venta_a_sheets(venta_test)
        
        if resultado["success"]:
            print(f"✅ Venta agregada exitosamente: {resultado}")
        else:
            print(f"⚠️  Venta no pudo ser agregada: {resultado}")
            # Verificar si es un error de permisos
            if "PERMISSION_DENIED" in resultado.get("error", ""):
                print("ℹ️  Error de permisos detectado correctamente")
            elif "GRID_LIMITS" in resultado.get("error", ""):
                print("ℹ️  Error de límites de grilla detectado correctamente")
            else:
                print(f"ℹ️  Otro tipo de error: {resultado.get('error', 'Desconocido')}")
        
    except Exception as e:
        print(f"❌ Error en test_error_handling: {e}")
        logger.error(f"Error en test_error_handling: {e}")

def main():
    """Función principal de pruebas"""
    print("INICIANDO PRUEBAS DE SERVICIOS ROBUSTOS")
    print("="*60)
    
    try:
        # Probar servicio de catálogo
        test_catalog_service()
        
        # Probar servicio de escritura
        test_google_sheets_writer()
        
        # Probar manejo de errores
        test_error_handling()
        
        print("\n" + "="*60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL EN LAS PRUEBAS: {e}")
        logger.error(f"Error general en las pruebas: {e}")

if __name__ == "__main__":
    main()

