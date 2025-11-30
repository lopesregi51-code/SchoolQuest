"""
Script para resetar o banco de dados do SchoolQuest
Apaga o banco de dados atual e cria um novo com dados iniciais
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, SessionLocal
from app import models, auth
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Reset database - drop all tables and recreate with initial data"""
    
    db_path = "schoolquest.db"
    
    # Close any existing connections
    engine.dispose()
    
    # Delete database file if exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            logger.info(f"✅ Banco de dados '{db_path}' deletado")
        except Exception as e:
            logger.error(f"❌ Erro ao deletar banco: {e}")
            return False
    
    # Create all tables
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("✅ Tabelas criadas com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        return False
    
    # Create initial data
    db = SessionLocal()
    try:
        # Create admin school
        admin_school = models.Escola(nome="Escola Administração")
        db.add(admin_school)
        db.flush()
        
        # Create admin user
        admin_user = models.User(
            email="admin@test.com",
            nome="Administrador",
            senha_hash=auth.get_password_hash("admin123"),
            papel="admin",
            escola_id=admin_school.id,
            pontos=1000,
            xp=1000,
            nivel=10,
            qr_token="admin-qr-token-unique"
        )
        db.add(admin_user)
        
        # Create demo school
        demo_school = models.Escola(nome="Escola Demo")
        db.add(demo_school)
        db.flush()
        
        # Create demo series
        serie_6ano = models.Serie(nome="6º Ano", escola_id=demo_school.id)
        serie_7ano = models.Serie(nome="7º Ano", escola_id=demo_school.id)
        db.add_all([serie_6ano, serie_7ano])
        db.flush()
        
        # Create manager
        gestor = models.User(
            email="gestor@test.com",
            nome="Gestor Demo",
            senha_hash=auth.get_password_hash("gestor123"),
            papel="gestor",
            escola_id=demo_school.id,
            qr_token="gestor-qr-token-unique"
        )
        db.add(gestor)
        
        # Create professor
        professor = models.User(
            email="professor@test.com",
            nome="Professor Demo",
            senha_hash=auth.get_password_hash("prof123"),
            papel="professor",
            escola_id=demo_school.id,
            disciplina="Matemática",
            qr_token="professor-qr-token-unique"
        )
        db.add(professor)
        
        # Create students
        aluno1 = models.User(
            email="aluno1@test.com",
            nome="João Silva",
            senha_hash=auth.get_password_hash("aluno123"),
            papel="aluno",
            escola_id=demo_school.id,
            serie_id=serie_6ano.id,
            xp=150,
            nivel=2,
            moedas=50,
            qr_token="aluno1-qr-token-unique"
        )
        
        aluno2 = models.User(
            email="aluno2@test.com",
            nome="Maria Santos",
            senha_hash=auth.get_password_hash("aluno123"),
            papel="aluno",
            escola_id=demo_school.id,
            serie_id=serie_6ano.id,
            xp=80,
            nivel=1,
            moedas=30,
            qr_token="aluno2-qr-token-unique"
        )
        
        db.add_all([aluno1, aluno2])
        db.commit()
        
        logger.info("✅ Dados iniciais criados com sucesso!")
        logger.info("\n" + "="*50)
        logger.info("📋 CREDENCIAIS DE ACESSO:")
        logger.info("="*50)
        logger.info("👤 Admin:")
        logger.info("   Email: admin@test.com")
        logger.info("   Senha: admin123")
        logger.info("\n👤 Gestor:")
        logger.info("   Email: gestor@test.com")
        logger.info("   Senha: gestor123")
        logger.info("\n👤 Professor:")
        logger.info("   Email: professor@test.com")
        logger.info("   Senha: prof123")
        logger.info("\n👤 Aluno 1:")
        logger.info("   Email: aluno1@test.com")
        logger.info("   Senha: aluno123")
        logger.info("\n👤 Aluno 2:")
        logger.info("   Email: aluno2@test.com")
        logger.info("   Senha: aluno123")
        logger.info("="*50 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar dados iniciais: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔄 RESETANDO BANCO DE DADOS...")
    print("⚠️  ATENÇÃO: Todos os dados serão perdidos!\n")
    
    confirm = input("Digite 'SIM' para confirmar: ")
    if confirm.upper() == "SIM":
        if reset_database():
            print("\n✅ Banco de dados resetado com sucesso!")
        else:
            print("\n❌ Erro ao resetar banco de dados")
    else:
        print("\n❌ Operação cancelada")
