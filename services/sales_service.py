from datetime import datetime
from threading import RLock
from .google_sheets_writer import GoogleSheetsWriter
from .apps_script_writer import AppsScriptWriter
from config import GOOGLE_APPS_SCRIPT

# Estructura en memoria
_ventas: list[dict] = []  # lista de dicts: {fecha,id,nombre,precio,unidades,total,pago,notas}
_ventas_lock = RLock()

# Instancia del escritor de Google Sheets (lazy)
_sheets_writer = None

def _get_sheets_writer():
    global _sheets_writer
    if _sheets_writer is None:
        try:
            # Forzar uso de API directa de Google Sheets para mayor confiabilidad ahora
            # Si deseas volver a Apps Script, comenta la línea siguiente y descomenta la lógica por GAS_URL.
            print("[INFO] Usando GoogleSheetsWriter (API directa), ignorando GAS_URL temporalmente")
            _sheets_writer = GoogleSheetsWriter()
            # -- Modo anterior por GAS_URL --
            # gas_url = (GOOGLE_APPS_SCRIPT.get("GAS_URL") or "").strip()
            # if gas_url:
            #     _sheets_writer = AppsScriptWriter()
            # else:
            #     _sheets_writer = GoogleSheetsWriter()
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
    # Permitir unidades negativas (devoluciones) y precios negativos si se desea registrar ajustes

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
    with _ventas_lock:
        return list(_ventas)

def agregar_venta(data: dict):
    """Agrega una venta solo a la memoria local (pendiente de exportar)."""
    venta = _normalizar_venta(data)
    with _ventas_lock:
        _ventas.append(venta)
    print(f"   NOTA: La venta NO se exportó a Google Sheets. Usa 'Exportar a Google Sheets' cuando estés listo.")

def actualizar_venta(index: int, data: dict):
    venta = _normalizar_venta(data)
    with _ventas_lock:
        if index < 0 or index >= len(_ventas):
            raise IndexError("Índice fuera de rango")
        _ventas[index] = venta

def eliminar_venta(index: int):
    with _ventas_lock:
        if index < 0 or index >= len(_ventas):
            raise IndexError("Índice fuera de rango")
        _ventas.pop(index)

def limpiar_ventas():
    """Elimina todas las ventas en memoria (no toca historial)."""
    with _ventas_lock:
        _ventas.clear()

def cargar_ventas_desde_historial():
    """Carga todas las ventas del historial persistente a la memoria al iniciar el servidor"""
    from .history_service import leer_historial
    try:
        hist = leer_historial()
        ventas_cargadas = 0
        for fecha, ventas_dia in hist.items():
            for venta in ventas_dia:
                with _ventas_lock:
                    _ventas.append(venta)
                ventas_cargadas += 1
        print(f"✅ Cargadas {ventas_cargadas} ventas desde historial persistente")
        return ventas_cargadas
    except Exception as e:
        print(f"⚠️ Error cargando ventas desde historial: {e}")
        return 0

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
    """Exporta TODAS las ventas acumuladas en memoria a Google Sheets en UNA sola actualización."""
    if not _ventas:
        return {
            "success": False,
            "error": "NO_HAY_VENTAS",
            "mensaje": "No hay ventas para exportar. Agrega algunas ventas primero."
        }

    try:
        writer = _get_sheets_writer()
        # Tomar snapshot inmutable para evitar desfasajes si se agregan ventas durante la exportación
        ventas_snapshot = list(_ventas)
        print(f"🚀 Exportando {len(ventas_snapshot)} ventas...")
        resultado = writer.agregar_multiples_ventas_a_sheets(ventas_snapshot)
        # Enriquecer respuesta con las ventas efectivamente exportadas
        try:
            indices = resultado.get("indices_exitosos") or list(range(len(ventas_snapshot)))
            ventas_ok = [ventas_snapshot[i] for i in indices if 0 <= i < len(ventas_snapshot)]
            resultado["ventas_exportadas_items"] = ventas_ok
        except Exception:
            # No romper si la respuesta no tiene indices
            pass
        return resultado
    except Exception as e:
        return {
            "success": False,
            "error": "EXPORT_ERROR",
            "mensaje": f"Error exportando ventas: {str(e)}"
        }
