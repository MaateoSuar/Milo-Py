import os
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime, date

# DB optional
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_DB = bool(DATABASE_URL)

if USE_DB:
    from sqlalchemy import select, delete, asc, func
    from .db import get_session, init_db
    from .models import Venta, StockIngreso

# JSON fallback paths
HIST_PATH = Path(__file__).resolve().parent.parent / 'data' / 'historial.json'
BACKUP_DIR = Path(__file__).resolve().parent.parent / 'backups'


def _ensure_file():
    HIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not HIST_PATH.exists():
        HIST_PATH.write_text('{}', encoding='utf-8')


def _crear_respaldo():
    # Si usamos DB, no generamos respaldos JSON
    if USE_DB:
        return
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"historial_backup_{timestamp}.json"
        if HIST_PATH.exists():
            backup_path.write_text(HIST_PATH.read_text(encoding='utf-8'), encoding='utf-8')
            print(f"✅ Respaldo creado: {backup_path.name}")
    except Exception as e:
        print(f"⚠️ Error creando respaldo: {e}")


def _venta_to_dict(v: 'Venta') -> dict:
    return {
        "fecha": v.fecha.strftime('%Y-%m-%d') if isinstance(v.fecha, date) else str(v.fecha),
        "id": v.producto_id,
        "nombre": v.nombre,
        "precio": float(v.precio),
        "unidades": int(v.unidades),
        "total": float(v.total),
        "pago": v.pago,
        "notas": v.notas or "",
        "costo_unitario": float(v.costo_unitario) if getattr(v, "costo_unitario", None) is not None else 0.0,
    }


def leer_historial() -> Dict[str, List[dict]]:
    if USE_DB:
        try:
            init_db()
            session = get_session()
            try:
                # Traer todas las ventas y agrupar por fecha
                rows = session.execute(select(Venta).order_by(asc(Venta.fecha), asc(Venta.created_at), asc(Venta.id))).scalars().all()
                hist: Dict[str, List[dict]] = {}
                for v in rows:
                    f = v.fecha.strftime('%Y-%m-%d') if isinstance(v.fecha, date) else str(v.fecha)[:10]
                    hist.setdefault(f, []).append(_venta_to_dict(v))
                return hist
            finally:
                session.close()
        except Exception as e:
            print(f"⚠️ Error leyendo historial desde DB, usando JSON fallback: {e}")
            # fallthrough a JSON
    # JSON fallback
    _ensure_file()
    try:
        raw = HIST_PATH.read_text(encoding='utf-8').strip() or '{}'
        data = json.loads(raw)
        if not isinstance(data, dict):
            return {}
        for k, v in list(data.items()):
            if not isinstance(v, list):
                data[k] = []
        return data
    except Exception:
        return {}


def guardar_historial(data: Dict[str, List[dict]]) -> None:
    # Solo aplica al modo JSON
    _ensure_file()
    _crear_respaldo()
    HIST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def agregar_ventas_a_historial(ventas: List[dict]) -> int:
    if not ventas:
        return 0
    if USE_DB:
        try:
            init_db()
            session = get_session()
            try:
                added = 0
                for v in ventas:
                    f = (v.get('fecha') or '').strip()[:10]
                    if not f:
                        continue

                    producto_id = str(v.get('id') or '').upper()
                    nombre = str(v.get('nombre') or '')
                    precio = float(v.get('precio') or 0)
                    unidades = int(v.get('unidades') or 0)
                    total = float(v.get('total') or (precio * unidades))
                    pago = str(v.get('pago') or '')
                    notas = str(v.get('notas') or '')

                    # Tomar costo_unitario del payload si viene (calculado por FIFO en sales_service),
                    # si no, dejar 0.0 como valor por defecto.
                    try:
                        costo_unitario_val = float(v.get('costo_unitario')) if 'costo_unitario' in v and v.get('costo_unitario') is not None else 0.0
                    except Exception:
                        costo_unitario_val = 0.0

                    venta = Venta(
                        fecha=datetime.fromisoformat(f).date(),
                        producto_id=producto_id,
                        nombre=nombre,
                        precio=precio,
                        costo_unitario=costo_unitario_val,
                        unidades=unidades,
                        total=total,
                        pago=pago,
                        notas=notas,
                    )
                    session.add(venta)
                    added += 1
                session.commit()
                return added
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as e:
            print(f"⚠️ Error agregando a historial en DB, usando JSON fallback: {e}")
            # fallthrough a JSON
    # JSON fallback
    hist = leer_historial()
    added = 0
    for v in ventas:
        fecha = (v.get('fecha') or '').strip()[:10]
        if not fecha:
            continue
        hist.setdefault(fecha, []).append(v)
        added += 1
    guardar_historial(hist)
    return added


def eliminar_historial_por_fecha_idx(fecha: str, idx: int) -> bool:
    if USE_DB:
        try:
            init_db()
            session = get_session()
            try:
                # Encontrar el registro por posición para esa fecha ordenado por created_at/id
                fdate = datetime.fromisoformat(fecha[:10]).date()
                rows = session.execute(
                    select(Venta).where(Venta.fecha == fdate).order_by(asc(Venta.created_at), asc(Venta.id))
                ).scalars().all()
                if idx < 0 or idx >= len(rows):
                    return False
                target = rows[idx]
                session.execute(delete(Venta).where(Venta.id == target.id))
                session.commit()
                return True
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as e:
            print(f"⚠️ Error eliminando historial en DB, usando JSON fallback: {e}")
            # fallthrough a JSON
    # JSON fallback
    hist = leer_historial()
    items = hist.get(fecha)
    if not isinstance(items, list):
        return False
    if idx < 0 or idx >= len(items):
        return False
    items.pop(idx)
    if len(items) == 0:
        hist.pop(fecha, None)
    else:
        hist[fecha] = items
    guardar_historial(hist)
    return True


def actualizar_historial_por_fecha_idx(fecha: str, idx: int, data: dict) -> bool:
    """Actualiza una venta del historial por fecha e índice relativo (modo DB/JSON).

    En modo DB, busca la venta por posición para esa fecha ordenando por
    created_at/id (igual que eliminar_historial_por_fecha_idx) y actualiza
    los campos básicos. En modo JSON, modifica directamente la estructura
    en memoria.
    """
    if USE_DB:
        try:
            init_db()
            session = get_session()
            try:
                fdate = datetime.fromisoformat(fecha[:10]).date()
                rows = session.execute(
                    select(Venta)
                    .where(Venta.fecha == fdate)
                    .order_by(asc(Venta.created_at), asc(Venta.id))
                ).scalars().all()
                if idx < 0 or idx >= len(rows):
                    return False
                v = rows[idx]

                # Actualizar campos si vienen en el payload
                new_fecha = (data.get('fecha') or '').strip()
                if new_fecha:
                    try:
                        v.fecha = datetime.fromisoformat(new_fecha[:10]).date()
                    except Exception:
                        pass

                if 'id' in data:
                    v.producto_id = str(data.get('id') or '').upper()
                if 'nombre' in data:
                    v.nombre = str(data.get('nombre') or '')

                if 'precio' in data:
                    try:
                        v.precio = float(data.get('precio') or 0)
                    except Exception:
                        pass
                if 'unidades' in data:
                    try:
                        v.unidades = int(data.get('unidades') or 0)
                    except Exception:
                        pass

                # Recalcular total si viene explícito o por precio*unidades
                if 'total' in data:
                    try:
                        v.total = float(data.get('total') or 0)
                    except Exception:
                        pass
                else:
                    try:
                        v.total = float(v.precio or 0) * int(v.unidades or 0)
                    except Exception:
                        pass

                if 'pago' in data:
                    v.pago = str(data.get('pago') or '')
                if 'notas' in data:
                    v.notas = str(data.get('notas') or '')

                session.commit()
                return True
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as e:
            print(f"⚠️ Error actualizando historial en DB, usando JSON fallback: {e}")

    # JSON fallback
    hist = leer_historial()
    items = hist.get(fecha)
    if not isinstance(items, list):
        return False
    if idx < 0 or idx >= len(items):
        return False

    current = items[idx]
    if not isinstance(current, dict):
        current = {}

    merged = dict(current)
    merged.update({
        k: v
        for k, v in data.items()
        if k in {"fecha", "id", "nombre", "precio", "unidades", "total", "pago", "notas"}
    })
    items[idx] = merged
    hist[fecha] = items
    guardar_historial(hist)
    return True
