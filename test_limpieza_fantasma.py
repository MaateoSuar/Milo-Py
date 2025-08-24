"""
Prueba de la nueva función de limpieza ULTRA-AGRESIVA de filas fantasma
"""
import logging
from services.google_sheets_writer import GoogleSheetsWriter

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_estado_detallado():
    """Prueba el análisis detallado de la hoja"""
    print("\n" + "="*60)
    print("ANÁLISIS DETALLADO DE LA HOJA")
    print("="*60)
    
    try:
        writer = GoogleSheetsWriter()
        print("✅ GoogleSheetsWriter inicializado")
        
        # Obtener estado detallado
        print("\n🔍 OBTENIENDO ANÁLISIS DETALLADO...")
        estado_detallado = writer.obtener_estado_detallado()
        
        if estado_detallado["success"]:
            print(f"✅ ANÁLISIS COMPLETADO:")
            print(f"   - Total filas detectadas: {estado_detallado['total_filas']}")
            print(f"   - Filas con datos: {estado_detallado['filas_con_datos']}")
            print(f"   - Filas vacías: {estado_detallado['filas_vacias']}")
            print(f"   - Resumen: {estado_detallado['resumen']}")
            
            # Mostrar análisis de filas problemáticas
            if estado_detallado['analisis_problematico']:
                print(f"\n📋 ANÁLISIS DE FILAS PROBLEMÁTICAS (primeras 10):")
                for fila in estado_detallado['analisis_problematico'][:10]:
                    print(f"   Fila {fila['numero']}: {fila['celdas_con_contenido']} celdas con contenido, {fila['celdas_vacias']} vacías")
                    if fila['contenido_ejemplo']:
                        print(f"     Ejemplos: {', '.join(fila['contenido_ejemplo'])}")
        else:
            print(f"❌ Error obteniendo análisis: {estado_detallado.get('error', 'Desconocido')}")
            return
        
    except Exception as e:
        print(f"❌ Error en test_estado_detallado: {e}")
        logger.error(f"Error en test_estado_detallado: {e}")

def test_limpieza_fantasma():
    """Prueba la limpieza ultra-agresiva de filas fantasma"""
    print("\n" + "="*60)
    print("PRUEBA DE LIMPIEZA ULTRA-AGRESIVA DE FILAS FANTASMA")
    print("="*60)
    
    try:
        writer = GoogleSheetsWriter()
        print("✅ GoogleSheetsWriter inicializado")
        
        # Estado antes de limpiar
        estado_antes = writer.obtener_estado_sheets()
        print(f"\n📊 ESTADO ANTES DE LIMPIAR:")
        print(f"   - Nombre hoja: {estado_antes['nombre_hoja']}")
        print(f"   - Total filas: {estado_antes['total_filas']}")
        print(f"   - Última fila: {estado_antes['ultima_fila']}")
        
        # Intentar limpieza ultra-agresiva
        print(f"\n🧹 INICIANDO LIMPIEZA ULTRA-AGRESIVA...")
        resultado_limpieza = writer.limpiar_filas_fantasma()
        
        if resultado_limpieza["success"]:
            print(f"✅ LIMPIEZA ULTRA-AGRESIVA EXITOSA:")
            print(f"   - Filas limpiadas: {resultado_limpieza['filas_limpiadas']}")
            print(f"   - Filas fantasma encontradas: {resultado_limpieza.get('filas_fantasma_encontradas', 'N/A')}")
            print(f"   - Filas con datos reales: {resultado_limpieza.get('filas_con_datos_reales', 'N/A')}")
            print(f"   - Total filas antes: {resultado_limpieza.get('total_filas_antes', 'N/A')}")
            print(f"   - Total filas después: {resultado_limpieza.get('total_filas_despues', 'N/A')}")
        else:
            print(f"❌ Error en limpieza ultra-agresiva: {resultado_limpieza.get('error', 'Desconocido')}")
            return
        
        # Obtener estado después de limpiar
        estado_despues = writer.obtener_estado_sheets()
        print(f"\n📊 ESTADO DESPUÉS DE LIMPIAR:")
        print(f"   - Total filas: {estado_despues['total_filas']}")
        print(f"   - Última fila: {estado_despues['ultima_fila']}")
        
        # Calcular espacio liberado
        filas_liberadas = estado_antes['total_filas'] - estado_despues['total_filas']
        if filas_liberadas > 0:
            print(f"\n🎉 ESPACIO LIBERADO:")
            print(f"   - Filas liberadas: {filas_liberadas}")
            print(f"   - Porcentaje de mejora: {(filas_liberadas/estado_antes['total_filas'])*100:.1f}%")
        else:
            print(f"\nℹ️ No se liberó espacio (no había filas fantasma)")
        
        # Probar si ahora se puede escribir
        print(f"\n✍️ PROBANDO ESCRITURA DESPUÉS DE LIMPIEZA...")
        venta_test = {
            "fecha": "2024-01-01",
            "notas": "Test después de limpieza ultra-agresiva",
            "id": "TEST003",
            "nombre": "Producto Test Limpieza Fantasma",
            "precio": 75.00,
            "unidades": 1,
            "pago": "Efectivo"
        }
        
        resultado_escritura = writer.agregar_venta_a_sheets(venta_test)
        if resultado_escritura["success"]:
            print(f"✅ ESCRITURA EXITOSA: {resultado_escritura['mensaje']}")
            print(f"   - Fila utilizada: {resultado_escritura['fila']}")
        else:
            print(f"⚠️ ESCRITURA FALLÓ: {resultado_escritura['mensaje']}")
            print(f"   - Error: {resultado_escritura.get('error', 'Desconocido')}")
        
    except Exception as e:
        print(f"❌ Error en test_limpieza_fantasma: {e}")
        logger.error(f"Error en test_limpieza_fantasma: {e}")

def main():
    """Función principal de pruebas"""
    print("INICIANDO PRUEBAS DE LIMPIEZA ULTRA-AGRESIVA")
    print("="*60)
    
    try:
        # Análisis detallado primero
        test_estado_detallado()
        
        # Probar limpieza ultra-agresiva
        test_limpieza_fantasma()
        
        print("\n" + "="*60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL EN LAS PRUEBAS: {e}")
        logger.error(f"Error general en las pruebas: {e}")

if __name__ == "__main__":
    main()

