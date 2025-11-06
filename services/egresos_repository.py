from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any

from .models import Egreso


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        # Espera formato YYYY-MM-DD
        return datetime.strptime(value, "%Y-%m-%d").date()
    raise ValueError("fecha inválida")


def _parse_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def guardar_egresos(session, egresos: List[Dict[str, Any]]) -> int:
    """Inserta egresos en bloque. Retorna cantidad insertada."""
    objetos = []
    for e in egresos or []:
        obj = Egreso(
            fecha=_parse_date(e.get("fecha")),
            motivo=str(e.get("motivo", ""))[:1024],
            costo=_parse_decimal(e.get("costo")),
            tipo=str(e.get("tipo", ""))[:50],
            pago=str(e.get("pago", ""))[:50],
            observaciones=(str(e.get("observaciones", "")) or None),
        )
        objetos.append(obj)
    if objetos:
        session.add_all(objetos)
    return len(objetos)


def listar_egresos_db(session, limit: int = 200) -> List[Egreso]:
    q = session.query(Egreso).order_by(Egreso.fecha.desc(), Egreso.id.desc()).limit(int(limit))
    return list(q)


def eliminar_egreso_db(session, egreso_id: int) -> bool:
    obj = session.query(Egreso).filter(Egreso.id == int(egreso_id)).first()
    if not obj:
        return False
    session.delete(obj)
    return True
