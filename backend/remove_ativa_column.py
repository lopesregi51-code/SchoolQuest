from sqlalchemy import create_engine, text
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_ativa_column():
    """Remove a coluna 'ativa' da tabela missoes se ela existir."""
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        try:
            # Tenta selecionar a coluna para ver se existe
            conn.execute(text("SELECT ativa FROM missoes LIMIT 1"))
            logger.info("Coluna 'ativa' existe. Removendo...")
            
            # Remove a coluna
            conn.execute(text("ALTER TABLE missoes DROP COLUMN ativa"))
            conn.commit()
            logger.info("Coluna 'ativa' removida com sucesso!")
        except Exception as e:
            if "does not exist" in str(e) or "no such column" in str(e):
                logger.info("Coluna 'ativa' não existe. Nada a fazer.")
            else:
                logger.error(f"Erro ao remover coluna: {e}")
                raise

if __name__ == "__main__":
    remove_ativa_column()
