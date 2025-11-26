import os
from sqlalchemy import create_engine, text

# Get DATABASE_URL from env or use the one from the app context if possible
# Assuming the user has the .env loaded or variables set as they are running the app.
# We will try to load .env just in case.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

if not DATABASE_URL:
    print("❌ DATABASE_URL no encontrada. Asegúrate de tener el archivo .env o las variables de entorno configuradas.")
    exit(1)

def migrate():
    print(f"🔌 Conectando a la base de datos...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        try:
            print("🔄 Intentando agregar columna 'costo_unitario' a la tabla 'ventas'...")
            # Postgres syntax
            connection.execute(text("ALTER TABLE ventas ADD COLUMN IF NOT EXISTS costo_unitario NUMERIC(12, 2);"))
            connection.commit()
            print("✅ Columna 'costo_unitario' agregada exitosamente (o ya existía).")
        except Exception as e:
            print(f"❌ Error al migrar: {e}")

if __name__ == "__main__":
    migrate()
