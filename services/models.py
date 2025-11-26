from sqlalchemy import Column, Integer, String, Date, Numeric, Text, DateTime, func
from .db import Base


class Venta(Base):
    __tablename__ = 'ventas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    producto_id = Column(String(50), nullable=False)
    nombre = Column(String(255), nullable=False)
    precio = Column(Numeric(12, 2), nullable=False)
    costo_unitario = Column(Numeric(12, 2), nullable=True)  # Costo al momento de la venta
    unidades = Column(Integer, nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    pago = Column(String(50), nullable=False)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class Egreso(Base):
    __tablename__ = 'egresos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    motivo = Column(Text, nullable=False)
    costo = Column(Numeric(12, 2), nullable=False)
    tipo = Column(String(50), nullable=False)  # Costo Fijo / Costo Variable
    pago = Column(String(50), nullable=False)  # Efectivo / Transferencia
    observaciones = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class StockIngreso(Base):
    """Ingresos de stock por pedido.

    Esta tabla se usa para construir el Historial de Ingresos y el Stock Actual
    consolidado por ID de artículo.
    """

    __tablename__ = 'stock_ingreso'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    id_articulo = Column(String(50), nullable=False)  # Debe existir en el catálogo Milo
    tipo = Column(String(50), nullable=False)         # Aritos, Anillos, Collar, etc.
    precio_individual = Column(Numeric(12, 2), nullable=True)  # Precio de venta referencial
    costo_individual = Column(Numeric(12, 2), nullable=False)  # Costo unitario real
    cantidad = Column(Integer, nullable=False)
    costo_total = Column(Numeric(14, 2), nullable=False)       # costo_individual * cantidad
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
