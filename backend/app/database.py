from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Configurações otimizadas para SQLite
sqlite_connect_args = {
    "check_same_thread": False,
    "timeout": 30,  # Aumenta timeout para evitar locks
}

# Configurações do engine
engine_config = {
    "connect_args": sqlite_connect_args if "sqlite" in settings.database_url else {},
    "pool_pre_ping": True,  # Verifica conexões antes de usar
    "pool_recycle": 1800,   # Recicla conexões a cada 30 min (evita desconexão do Render)
}

# Se for SQLite, adiciona configurações específicas
if "sqlite" in settings.database_url:
    engine_config["poolclass"] = pool.StaticPool
else:
    # Configurações para PostgreSQL (Render)
    engine_config["pool_size"] = 10      # Aumenta pool base (padrão é 5)
    engine_config["max_overflow"] = 20   # Aumenta overflow (padrão é 10)
    engine_config["pool_timeout"] = 30   # Timeout em segundos

engine = create_engine(settings.database_url, **engine_config)

# Configurar WAL mode para SQLite (melhor concorrência)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configura pragmas do SQLite para melhor performance e confiabilidade."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_conn.cursor()
        # WAL mode permite leituras durante escritas
        cursor.execute("PRAGMA journal_mode=WAL")
        # Sincronização normal (balance entre segurança e performance)
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Cache maior
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB
        # Timeout para locks
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 segundos
        cursor.close()
        logger.info("SQLite pragmas configured for better reliability")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
