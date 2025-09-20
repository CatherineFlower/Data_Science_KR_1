from sqlalchemy import create_engine
engine = create_engine(
    "postgresql+psycopg2://USER:PASSWORD@HOST:5432/DB?sslmode=require",
    future=True, pool_pre_ping=True
)

# sanity check
with engine.connect() as conn:
    conn.exec_driver_sql("SET search_path TO ddos_app, public")
    conn.exec_driver_sql("SELECT 1")
