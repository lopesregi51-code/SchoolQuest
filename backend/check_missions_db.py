"""
Script para verificar missões no banco de dados
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models

def check_missions():
    db = SessionLocal()
    try:
        # Count total missions
        total_missions = db.query(models.Missao).count()
        print(f"\n=== VERIFICAÇÃO DE MISSÕES ===")
        print(f"Total de missões no banco: {total_missions}")
        
        if total_missions == 0:
            print("\n⚠️  PROBLEMA: Nenhuma missão encontrada no banco de dados!")
            print("   Crie missões pelo painel do professor primeiro.\n")
            return
        
        # List all missions
        print(f"\n=== LISTA DE MISSÕES ===")
        missoes = db.query(models.Missao).all()
        for missao in missoes:
            criador = db.query(models.User).filter(models.User.id == missao.criador_id).first()
            print(f"\nID: {missao.id}")
            print(f"  Título: {missao.titulo}")
            print(f"  Tipo: {missao.tipo}")
            print(f"  Criador: {criador.nome if criador else 'N/A'} (ID: {missao.criador_id})")
            if criador:
                print(f"  Escola do Criador: {criador.escola_id}")
        
        # Count students
        total_students = db.query(models.User).filter(models.User.papel == 'aluno').count()
        print(f"\n=== ALUNOS ===")
        print(f"Total de alunos: {total_students}")
        
        if total_students > 0:
            print("\nPrimeiros 5 alunos:")
            students = db.query(models.User).filter(models.User.papel == 'aluno').limit(5).all()
            for student in students:
                print(f"  - {student.nome} (escola_id: {student.escola_id})")
        
        # Count completed missions
        total_completed = db.query(models.MissaoConcluida).count()
        print(f"\n=== MISSÕES CONCLUÍDAS ===")
        print(f"Total de conclusões: {total_completed}")
        
        if total_completed > 0:
            print("\nÚltimas 5 conclusões:")
            completed = db.query(models.MissaoConcluida).order_by(models.MissaoConcluida.data_solicitacao.desc()).limit(5).all()
            for c in completed:
                print(f"  - Missão: {c.missao.titulo}")
                print(f"    Aluno: {c.aluno.nome}")
                print(f"    Validada: {'Sim' if c.validada else 'Não'}")
        
        print("\n" + "="*50 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}\n")
    finally:
        db.close()

if __name__ == "__main__":
    check_missions()
