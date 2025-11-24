"""
Script de inicialização do banco de dados para produção (Render).
Cria usuário admin e dados essenciais.
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import models, auth
from app.database import Base, engine
from app.config import settings

def init_database():
    """Initialize database with essential data."""
    print("🚀 Initializing database...")
    
    # Create all tables
    print("📋 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(models.User).filter(models.User.email == "admin@test.com").first()
        
        if not admin:
            print("👤 Creating admin user...")
            
            # Create admin school first
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
                nivel=10
            )
            db.add(admin_user)
            db.commit()
            
            print(f"✅ Admin user created: admin@test.com / admin123")
            print(f"✅ Admin school created: {admin_school.nome} (ID: {admin_school.id})")
        else:
            print(f"ℹ️  Admin user already exists: {admin.email}")
            
            # Ensure admin has a school
            if not admin.escola_id:
                print("🏫 Admin has no school, creating one...")
                admin_school = models.Escola(nome="Escola Administração")
                db.add(admin_school)
                db.flush()
                admin.escola_id = admin_school.id
                db.commit()
                print(f"✅ Admin school created and assigned: {admin_school.nome}")
        
        print("✅ Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print(f"📊 Database URL: {settings.database_url[:50]}...")
    print(f"🌍 Environment: {settings.environment}")
    init_database()
