"""
Script to seed the database with initial data (School, Users, Series, Missions).
Run this script from the backend directory:
python scripts/seed_data.py
"""
import sys
import os

# Add the parent directory to sys.path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app import models, auth
from sqlalchemy.orm import Session

def init_db():
    models.Base.metadata.create_all(bind=engine)

def get_or_create_school(db: Session, nome: str):
    school = db.query(models.Escola).filter(models.Escola.nome == nome).first()
    if not school:
        school = models.Escola(nome=nome)
        db.add(school)
        db.commit()
        db.refresh(school)
        print(f"[OK] Created School: {nome}")
    else:
        print(f"[SKIP] School already exists: {nome}")
    return school

def get_or_create_user(db: Session, nome, email, senha, papel, escola_id=None, serie_id=None):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            nome=nome,
            email=email,
            senha_hash=auth.get_password_hash(senha),
            papel=papel,
            escola_id=escola_id,
            serie_id=serie_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[OK] Created User: {email} ({papel})")
    else:
        print(f"[SKIP] User already exists: {email}")
    return user

def get_or_create_serie(db: Session, nome: str, escola_id: int):
    serie = db.query(models.Serie).filter(models.Serie.nome == nome, models.Serie.escola_id == escola_id).first()
    if not serie:
        serie = models.Serie(nome=nome, escola_id=escola_id)
        db.add(serie)
        db.commit()
        db.refresh(serie)
        print(f"[OK] Created Serie: {nome}")
    else:
        print(f"[SKIP] Serie already exists: {nome}")
    return serie

def seed_missions(db: Session, professor_id: int):
    missoes_demo = [
        {
            "titulo": "Resolver 10 exercícios de Matemática",
            "descricao": "Complete os exercícios 1-10 da página 45 do livro didático",
            "pontos": 50,
            "moedas": 20,
            "categoria": "diaria",
            "criador_id": professor_id
        },
        {
            "titulo": "Leitura: Capítulo 3 - Dom Casmurro",
            "descricao": "Leia o capítulo 3 e faça um resumo de 10 linhas",
            "pontos": 40,
            "moedas": 15,
            "categoria": "semanal",
            "criador_id": professor_id
        },
        {
            "titulo": "Presença na Aula de Inglês",
            "descricao": "Compareça e participe ativamente da aula",
            "pontos": 10,
            "moedas": 5,
            "categoria": "diaria",
            "criador_id": professor_id
        }
    ]

    count = 0
    for missao_data in missoes_demo:
        exists = db.query(models.Missao).filter(models.Missao.titulo == missao_data["titulo"]).first()
        if not exists:
            missao = models.Missao(**missao_data)
            db.add(missao)
            count += 1
    
    db.commit()
    if count > 0:
        print(f"[OK] Created {count} demo missions")
    else:
        print("[SKIP] Missions already exist")

def main():
    print("=== Seeding Database ===")
    init_db()
    db = SessionLocal()
    
    try:
        # 1. Create School
        school = get_or_create_school(db, "Escola Teste")
        
        # 2. Create Series
        serie_5a = get_or_create_serie(db, "5º Ano A", school.id)
        serie_5b = get_or_create_serie(db, "5º Ano B", school.id)

        # 3. Create Users
        admin = get_or_create_user(db, "Admin User", "admin@test.com", "admin123", "admin", escola_id=school.id)
        gestor = get_or_create_user(db, "Gestor Teste", "gestor@test.com", "gestor123", "gestor", escola_id=school.id)
        prof = get_or_create_user(db, "Professor Teste", "prof@test.com", "prof123", "professor", escola_id=school.id)
        
        # Aluno linked to Serie
        aluno = get_or_create_user(db, "Aluno Teste", "aluno@test.com", "aluno123", "aluno", escola_id=school.id, serie_id=serie_5a.id)

        # 4. Create Missions
        seed_missions(db, prof.id)

        print("\n=== Seeding Complete ===")
        
    except Exception as e:
        print(f"\n[ERROR] Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
