"""
Prueba de la nueva función de limpieza agresiva de filas vacías
"""
import logging
from services.google_sheets_writer import GoogleSheetsWriter

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_limpieza_agresiva():
    """Prueba la limpieza agresiva de filas vacías"""
    print("\n" + "="*60)
    print("PRUEBA DE LIMPIEZA AGRESIVA DE FILAS VACÍAS")
    print("="*60)
    
    try:
        writer = GoogleSheetsWriter()
        print("✅ GoogleSheetsWriter inicializado")
        
        # Obtener estado antes de limpiar
        estado_antes = writer.obtener_estado_sheets()
        print(f"\n📊 ESTADO ANTES DE LIMPIAR:")
        print(f"   - Nombre hoja: {estado_antes['nombre_hoja']}")
        print(f"   - Total filas: {estado_antes['total_filas']}")
        print(f"   - Última fila: {estado_antes['ultima_fila']}")
        print(f"   - Hoja protegida: {estado_antes.get('hoja_protegida', 'Desconocido')}")
        
        # Intentar limpieza agresiva
        print(f"\n🧹 INICIANDO LIMPIEZA AGRESIVA...")
        resultado_limpieza = writer.limpiar_filas_vacias_agresiva()
        
        if resultado_limpieza["success"]:
            print(f"✅ LIMPIEZA AGRESIVA EXITOSA:")
            print(f"   - Filas limpiadas: {resultado_limpieza['filas_limpiadas']}")
            print(f"   - Filas vacías encontradas: {resultado_limpieza.get('filas_vacias_encontradas', 'N/A')}")
            print(f"   - Filas con datos: {resultado_limpieza.get('filas_con_datos', 'N/A')}")
        else:
            print(f"❌ Error en limpieza agresiva: {resultado_limpieza.get('error', 'Desconocido')}")
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
            print(f"\nℹ️ No se liberó espacio (no había filas vacías)")
        
        # Probar si ahora se puede escribir
        print(f"\n✍️ PROBANDO ESCRITURA DESPUÉS DE LIMPIEZA...")
        venta_test = {
            "fecha": "2024-01-01",
            "notas": "Test después de limpieza agresiva",
            "id": "TEST002",
            "nombre": "Producto Test Limpieza",
            "precio": 50.00,
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
        print(f"❌ Error en test_limpieza_agresiva: {e}")
        logger.error(f"Error en test_limpieza_agresiva: {e}")

def test_limpieza_normal_vs_agresiva():
    """Compara la limpieza normal vs agresiva"""
    print("\n" + "="*60)
    print("COMPARACIÓN: LIMPIEZA NORMAL VS AGRESIVA")
    print("="*60)
    
    try:
        writer = GoogleSheetsWriter()
        print("✅ GoogleSheetsWriter inicializado")
        
        # Estado inicial
        estado_inicial = writer.obtener_estado_sheets()
        print(f"\n📊 ESTADO INICIAL:")
        print(f"   - Total filas: {estado_inicial['total_filas']}")
        print(f"   - Última fila: {estado_inicial['ultima_fila']}")
        
        # Limpieza normal
        print(f"\n🧹 LIMPIEZA NORMAL...")
        resultado_normal = writer.limpiar_filas_vacias()
        print(f"   - Resultado: {resultado_normal['filas_limpiadas']} filas limpiadas")
        
        # Estado después de limpieza normal
        estado_normal = writer.obtener_estado_sheets()
        print(f"   - Total filas después: {estado_normal['total_filas']}")
        
        # Limpieza agresiva
        print(f"\n🧹 LIMPIEZA AGRESIVA...")
        resultado_agresiva = writer.limpiar_filas_vacias_agresiva()
        print(f"   - Resultado: {resultado_agresiva['filas_limpiadas']} filas limpiadas")
        
        # Estado final
        estado_final = writer.obtener_estado_sheets()
        print(f"   - Total filas final: {estado_final['total_filas']}")
        
        # Resumen
        print(f"\n📈 RESUMEN DE LIMPIEZA:")
        print(f"   - Limpieza normal: {resultado_normal['filas_limpiadas']} filas")
        print(f"   - Limpieza agresiva: {resultado_agresiva['filas_limpiadas']} filas")
        print(f"   - Total liberado: {estado_inicial['total_filas'] - estado_final['total_filas']} filas")
        
    except Exception as e:
        print(f"❌ Error en comparación: {e}")
        logger.error(f"Error en comparación: {e}")

def main():
    """Función principal de pruebas"""
    print("INICIANDO PRUEBAS DE LIMPIEZA AGRESIVA")
    print("="*60)
    
    try:
        # Probar limpieza agresiva
        test_limpieza_agresiva()
        
        # Comparar métodos
        test_limpieza_normal_vs_agresiva()
        
        print("\n" + "="*60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL EN LAS PRUEBAS: {e}")
        logger.error(f"Error general en las pruebas: {e}")

if __name__ == "__main__":
    main()

