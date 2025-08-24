"""
Prueba de las nuevas funciones para manejar hojas llenas
"""
import logging
from services.google_sheets_writer import GoogleSheetsWriter

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_limpiar_filas_vacias():
    """Prueba la limpieza de filas vacías"""
    print("\n" + "="*50)
    print("PRUEBA DE LIMPIEZA DE FILAS VACÍAS")
    print("="*50)
    
    try:
        writer = GoogleSheetsWriter()
        print("✅ GoogleSheetsWriter inicializado")
        
        # Obtener estado antes de limpiar
        estado_antes = writer.obtener_estado_sheets()
        print(f"📊 Estado antes de limpiar:")
        print(f"   - Total filas: {estado_antes['total_filas']}")
        print(f"   - Última fila: {estado_antes['ultima_fila']}")
        print(f"   - Hoja protegida: {estado_antes.get('hoja_protegida', 'Desconocido')}")
        
        # Intentar limpiar filas vacías
        print("\n🧹 Limpiando filas vacías...")
        resultado_limpieza = writer.limpiar_filas_vacias()
        
        if resultado_limpieza["success"]:
            print(f"✅ Limpieza exitosa:")
            print(f"   - Filas limpiadas: {resultado_limpieza['filas_limpiadas']}")
            if 'nueva_ultima_fila' in resultado_limpieza:
                print(f"   - Nueva última fila: {resultado_limpieza['nueva_ultima_fila']}")
        else:
            print(f"❌ Error en limpieza: {resultado_limpieza.get('error', 'Desconocido')}")
        
        # Obtener estado después de limpiar
        estado_despues = writer.obtener_estado_sheets()
        print(f"\n📊 Estado después de limpiar:")
        print(f"   - Total filas: {estado_despues['total_filas']}")
        print(f"   - Última fila: {estado_despues['ultima_fila']}")
        
    except Exception as e:
        print(f"❌ Error en test_limpiar_filas_vacias: {e}")
        logger.error(f"Error en test_limpiar_filas_vacias: {e}")

def test_crear_nueva_hoja():
    """Prueba la creación de una nueva hoja"""
    print("\n" + "="*50)
    print("PRUEBA DE CREACIÓN DE NUEVA HOJA")
    print("="*50)
    
    try:
        writer = GoogleSheetsWriter()
        print("✅ GoogleSheetsWriter inicializado")
        
        # Obtener estado de la hoja actual
        estado_actual = writer.obtener_estado_sheets()
        print(f"📊 Estado de la hoja actual:")
        print(f"   - Nombre: {estado_actual['nombre_hoja']}")
        print(f"   - Total filas: {estado_actual['total_filas']}")
        print(f"   - Última fila: {estado_actual['ultima_fila']}")
        
        # Crear nueva hoja
        print("\n🆕 Creando nueva hoja...")
        resultado_nueva = writer.crear_nueva_hoja()
        
        if resultado_nueva["success"]:
            print(f"✅ Nueva hoja creada exitosamente:")
            print(f"   - Nombre: {resultado_nueva['nombre_hoja']}")
            print(f"   - URL: {resultado_nueva['url']}")
            print(f"   - Mensaje: {resultado_nueva['mensaje']}")
            
            # Obtener estado de la nueva hoja
            estado_nueva = writer.obtener_estado_sheets()
            print(f"\n📊 Estado de la nueva hoja:")
            print(f"   - Nombre: {estado_nueva['nombre_hoja']}")
            print(f"   - Total filas: {estado_nueva['total_filas']}")
            print(f"   - Última fila: {estado_nueva['ultima_fila']}")
            
            # Probar escribir en la nueva hoja
            print("\n✍️ Probando escritura en la nueva hoja...")
            venta_test = {
                "fecha": "2024-01-01",
                "notas": "Test en nueva hoja",
                "id": "TEST001",
                "nombre": "Producto Test Nueva Hoja",
                "precio": 100.00,
                "unidades": 1,
                "pago": "Efectivo"
            }
            
            resultado_escritura = writer.agregar_venta_a_sheets(venta_test)
            if resultado_escritura["success"]:
                print(f"✅ Escritura exitosa en nueva hoja: {resultado_escritura['mensaje']}")
            else:
                print(f"⚠️ Escritura falló: {resultado_escritura['mensaje']}")
                
        else:
            print(f"❌ Error creando nueva hoja: {resultado_nueva.get('error', 'Desconocido')}")
        
    except Exception as e:
        print(f"❌ Error en test_crear_nueva_hoja: {e}")
        logger.error(f"Error en test_crear_nueva_hoja: {e}")

def main():
    """Función principal de pruebas"""
    print("INICIANDO PRUEBAS DE MANEJO DE HOJAS LLENAS")
    print("="*60)
    
    try:
        # Probar limpieza de filas vacías
        test_limpiar_filas_vacias()
        
        # Probar creación de nueva hoja
        test_crear_nueva_hoja()
        
        print("\n" + "="*60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL EN LAS PRUEBAS: {e}")
        logger.error(f"Error general en las pruebas: {e}")

if __name__ == "__main__":
    main()

