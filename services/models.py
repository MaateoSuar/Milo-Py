from sqlalchemy import Column, Integer, String, Date, Numeric, Text, DateTime, func
from .db import Base

class Venta(Base):
    __tablename__ = 'ventas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    producto_id = Column(String(50), nullable=False)
    nombre = Column(String(255), nullable=False)
    precio = Column(Numeric(12, 2), nullable=False)
    unidades = Column(Integer, nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    pago = Column(String(50), nullable=False)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
