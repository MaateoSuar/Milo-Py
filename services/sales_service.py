from datetime import datetime
from .google_sheets_writer import GoogleSheetsWriter

# Estructura en memoria
_ventas = []  # lista de dicts: {fecha,id,nombre,precio,unidades,total,pago,notas}

# Instancia del escritor de Google Sheets
_sheets_writer = GoogleSheetsWriter()

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
    venta = _normalizar_venta(data)
    _ventas.append(venta)
    
    # Agregar también al Google Sheet
    try:
        resultado = _sheets_writer.agregar_venta_a_sheets(venta)
        if resultado["success"]:
            print(f"✅ Venta agregada a Google Sheets en fila {resultado['fila']}")
        else:
            print(f"⚠️ Error agregando a Google Sheets: {resultado['error']}")
    except Exception as e:
        print(f"⚠️ Error con Google Sheets: {e}")

def actualizar_venta(index: int, data: dict):
    if index < 0 or index >= len(_ventas):
        raise IndexError("Índice fuera de rango")
    venta = _normalizar_venta(data)
    _ventas[index] = venta

def eliminar_venta(index: int):
    if index < 0 or index >= len(_ventas):
        raise IndexError("Índice fuera de rango")
    _ventas.pop(index)

def obtener_estado_sheets():
    """Obtiene el estado del Google Sheet"""
    return _sheets_writer.obtener_estado_sheets()
