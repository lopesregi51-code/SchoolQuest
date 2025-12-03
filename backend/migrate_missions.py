from sqlalchemy import create_engine, text
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        try:
            # Tenta selecionar a coluna para ver se existe
            conn.execute(text("SELECT ativa FROM missoes LIMIT 1"))
            logger.info("Coluna 'ativa' já existe.")
        except Exception:
            logger.info("Adicionando coluna 'ativa'...")
            # Adiciona a coluna se der erro (não existe)
            if "sqlite" in settings.database_url:
                conn.execute(text("ALTER TABLE missoes ADD COLUMN ativa BOOLEAN DEFAULT 1"))
            else:
                conn.execute(text("ALTER TABLE missoes ADD COLUMN ativa BOOLEAN DEFAULT TRUE"))
            conn.commit()
            logger.info("Coluna 'ativa' adicionada com sucesso!")

if __name__ == "__main__":
    migrate()
