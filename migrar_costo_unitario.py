import sqlalchemy as sa

URL = (
    "postgresql+psycopg2://postgres:"
    "jwLwYrTMTPSpHGgWkoNNBklHkDKXFyEV"
    "@interchange.proxy.rlwy.net:48661/railway"
)

engine = sa.create_engine(URL)

with engine.connect() as conn:
    conn.execute(sa.text(
        "ALTER TABLE ventas "
        "ADD COLUMN IF NOT EXISTS costo_unitario numeric(12, 2)"
    ))
    conn.commit()

print("ALTER TABLE ejecutado correctamente")