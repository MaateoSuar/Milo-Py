from datetime import datetime
from .google_sheets_writer import GoogleSheetsWriter

# Estructura en memoria
_ventas = []  # lista de dicts: {fecha,id,nombre,precio,unidades,total,pago,notas}

# Instancia del escritor de Google Sheets (lazy)
_sheets_writer = None

def _get_sheets_writer():
    global _sheets_writer
    if _sheets_writer is None:
        try:
            _sheets_writer = GoogleSheetsWriter()
        except Exception as e:
            print(f"⚠️ No se pudo inicializar GoogleSheetsWriter: {e}")
            _sheets_writer = None
    return _sheets_writer

def _normalizar_venta(data: dict) -> dict:
    """
    Valida y normaliza una venta. Calcula 'total' en servidor.
    """
    required = ["fecha", "id", "nombre", "precio", "unidades", "pago"]
    for k in required:
        if k not in data or data[k] in (None, ""):
            raise ValueError(f"Falta el campo requerido: {k}")

    # fecha en formato YYYY-MM-DD
    try:
        fecha_str = str(data["fecha"]).strip()
        # Permite 'YYYY-MM-DD' o fecha compatible
        _ = datetime.fromisoformat(fecha_str)
        fecha = fecha_str[:10]
    except Exception:
        raise ValueError("Fecha inválida (use YYYY-MM-DD)")

    id_prod = str(data["id"]).strip().upper()
    nombre = str(data["nombre"]).strip()

    try:
        precio = float(data["precio"])
    except Exception:
        raise ValueError("Precio inválido")

    try:
        unidades = int(data["unidades"])
    except Exception:
        raise ValueError("Unidades inválidas")

    if unidades < 1:
        raise ValueError("Unidades debe ser >= 1")
    if precio < 0:
        raise ValueError("Precio no puede ser negativo")

    pago = str(data["pago"]).strip() or "Otro"
    notas = str(data.get("notas", "") or "").strip()

    total = round(precio * unidades, 2)

    return {
        "fecha": fecha,
        "id": id_prod,
        "nombre": nombre,
        "precio": float(precio),
        "unidades": int(unidades),
        "total": float(total),
        "pago": pago,
        "notas": notas
    }

def listar_ventas():
    return list(_ventas)

def agregar_venta(data: dict):
    """Agrega una venta SOLO a la memoria local, NO a Google Sheets automáticamente"""
    venta = _normalizar_venta(data)
    _ventas.append(venta)
    print(f"✅ Venta agregada a la memoria local (índice: {len(_ventas) - 1})")
    print(f"   NOTA: La venta NO se exportó a Google Sheets. Usa 'Exportar a Google Sheets' cuando estés listo.")

def actualizar_venta(index: int, data: dict):
    if index < 0 or index >= len(_ventas):
        raise IndexError("Índice fuera de rango")
    venta = _normalizar_venta(data)
    _ventas[index] = venta

def eliminar_venta(index: int):
    if index < 0 or index >= len(_ventas):
        raise IndexError("Índice fuera de rango")
    _ventas.pop(index)

def limpiar_ventas():
    """Elimina todas las ventas en memoria"""
    _ventas.clear()

def obtener_estado_sheets():
    """Obtiene el estado del Google Sheet"""
    writer = _get_sheets_writer()
    if writer is None:
        return {
            "success": False,
            "error": "GOOGLE_SHEETS_NOT_AVAILABLE",
            "mensaje": "Credenciales de Google Sheets no disponibles"
        }
    return writer.obtener_estado_sheets()

def exportar_todas_las_ventas_a_sheets():
    """Exporta TODAS las ventas acumuladas en memoria a Google Sheets de forma RÁPIDA"""
    if not _ventas:
        return {
            "success": False,
            "error": "NO_HAY_VENTAS",
            "mensaje": "No hay ventas para exportar. Agrega algunas ventas primero."
        }
    
    try:
        print(f"🚀 Exportando {len(_ventas)} ventas a Google Sheets (MODO RÁPIDO)...")
        
        writer = _get_sheets_writer()
        if writer is None:
            return {
                "success": False,
                "error": "GOOGLE_SHEETS_NOT_AVAILABLE",
                "mensaje": "Credenciales de Google Sheets no disponibles"
            }

        # Usar el método de escritura en lote para máxima velocidad
        resultado = writer.agregar_multiples_ventas_a_sheets(_ventas)
        
        if resultado["success"]:
            print(f"✅ {len(_ventas)} ventas exportadas exitosamente a Google Sheets")
            
            # OPCIONAL: Limpiar ventas después de exportar exitosamente
            # ventas_exportadas = _ventas.copy()
            # _ventas.clear()
            # print(f"🧹 Ventas limpiadas de la memoria local después de exportar")
            
            return {
                "success": True,
                "ventas_exportadas": len(_ventas),
                "mensaje": f"Exportado con éxito"
            }
        else:
            print(f"❌ Error exportando ventas: {resultado.get('error', 'Error desconocido')}")
            return resultado
            
    except Exception as e:
        error_msg = f"Error exportando ventas: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": "EXPORT_ERROR",
            "mensaje": error_msg
        }
