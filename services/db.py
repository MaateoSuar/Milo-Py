import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy recomienda el esquema postgresql+psycopg2
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

Base = declarative_base()
_engine = None
SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL no configurada")
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


def get_session():
    global SessionLocal
    if SessionLocal is None:
        engine = get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_db():
    if not DATABASE_URL:
        return False
    engine = get_engine()
    # Importar modelos aquí para registrar metadata
    from .models import Venta, Egreso, StockIngreso  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # Pequeña migración segura: agregar columna costo_unitario si no existe
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    "ALTER TABLE ventas "
                    "ADD COLUMN IF NOT EXISTS costo_unitario numeric(12, 2)"
                )
            )
    except Exception:
        # No romper si la migración falla; el resto de la app puede seguir usando JSON
        pass
    return True
