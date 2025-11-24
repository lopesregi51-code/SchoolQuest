"""
CSV processing handlers for bulk import
"""
import pandas as pd
import io
from sqlalchemy.orm import Session
from fastapi import HTTPException
from . import models, auth
import logging

logger = logging.getLogger(__name__)


def process_escolas_csv(df: pd.DataFrame, db: Session) -> dict:
    """Process schools CSV file"""
    created = []
    errors = []
    
    # Validate columns
    if 'nome' not in df.columns:
        raise HTTPException(400, "CSV deve conter coluna 'nome'")
    
    for idx, row in df.iterrows():
        try:
            # Validate
            if pd.isna(row['nome']) or str(row['nome']).strip() == '':
                errors.append(f"Linha {idx+2}: Nome obrigatório")
                continue
            
            nome = str(row['nome']).strip()
            
            # Check if already exists
            existing = db.query(models.Escola).filter(models.Escola.nome == nome).first()
            if existing:
                errors.append(f"Linha {idx+2}: Escola '{nome}' já existe")
                continue
            
            # Create school
            escola = models.Escola(nome=nome)
            db.add(escola)
            db.commit()
            db.refresh(escola)
            created.append(nome)
            logger.info(f"Escola criada via CSV: {nome}")
            
        except Exception as e:
            db.rollback()
            errors.append(f"Linha {idx+2}: {str(e)}")
            logger.error(f"Error processing escola CSV row {idx}: {e}")
    
    return {
        "success": len(created),
        "errors": len(errors),
        "created": created,
        "error_details": errors
    }


def process_gestores_csv(df: pd.DataFrame, db: Session) -> dict:
    """Process managers CSV file"""
    created = []
    errors = []
    
    # Validate columns
    required_cols = ['nome', 'email', 'senha', 'escola_nome']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(400, f"CSV deve conter colunas: {', '.join(missing)}")
    
    for idx, row in df.iterrows():
        try:
            # Validate required fields
            nome = str(row['nome']).strip() if not pd.isna(row['nome']) else ''
            email = str(row['email']).strip().lower() if not pd.isna(row['email']) else ''
            senha = str(row['senha']).strip() if not pd.isna(row['senha']) else ''
            escola_nome = str(row['escola_nome']).strip() if not pd.isna(row['escola_nome']) else ''
            
            if not nome or not email or not senha or not escola_nome:
                errors.append(f"Linha {idx+2}: Todos os campos são obrigatórios")
                continue
            
            # Validate password length
            if len(senha) < 6:
                errors.append(f"Linha {idx+2}: Senha deve ter no mínimo 6 caracteres")
                continue
            
            # Check if email already exists
            existing_user = db.query(models.User).filter(models.User.email == email).first()
            if existing_user:
                errors.append(f"Linha {idx+2}: Email '{email}' já cadastrado")
                continue
            
            # Find school
            escola = db.query(models.Escola).filter(models.Escola.nome == escola_nome).first()
            if not escola:
                errors.append(f"Linha {idx+2}: Escola '{escola_nome}' não encontrada")
                continue
            
            # Create manager
            gestor = models.User(
                email=email,
                nome=nome,
                senha_hash=auth.get_password_hash(senha),
                papel='gestor',
                escola_id=escola.id
            )
            db.add(gestor)
            db.commit()
            db.refresh(gestor)
            created.append(f"{nome} ({email})")
            logger.info(f"Gestor criado via CSV: {email}")
            
        except Exception as e:
            db.rollback()
            errors.append(f"Linha {idx+2}: {str(e)}")
            logger.error(f"Error processing gestor CSV row {idx}: {e}")
    
    return {
        "success": len(created),
        "errors": len(errors),
        "created": created,
        "error_details": errors
    }


def process_usuarios_csv(df: pd.DataFrame, db: Session) -> dict:
    """Process users (students/professors) CSV file"""
    created = []
    errors = []
    
    # Validate columns
    required_cols = ['nome', 'email', 'senha', 'papel', 'escola_nome']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(400, f"CSV deve conter colunas: {', '.join(missing)}")
    
    # Optional columns
    if 'serie' not in df.columns:
        df['serie'] = ''
    if 'disciplina' not in df.columns:
        df['disciplina'] = ''
    
    for idx, row in df.iterrows():
        try:
            # Parse fields
            nome = str(row['nome']).strip() if not pd.isna(row['nome']) else ''
            email = str(row['email']).strip().lower() if not pd.isna(row['email']) else ''
            senha = str(row['senha']).strip() if not pd.isna(row['senha']) else ''
            papel = str(row['papel']).strip().lower() if not pd.isna(row['papel']) else ''
            escola_nome = str(row['escola_nome']).strip() if not pd.isna(row['escola_nome']) else ''
            serie_nome = str(row['serie']).strip() if not pd.isna(row['serie']) else ''
            disciplina = str(row['disciplina']).strip() if not pd.isna(row['disciplina']) else ''
            
            # Validate required
            if not nome or not email or not senha or not papel or not escola_nome:
                errors.append(f"Linha {idx+2}: Campos obrigatórios: nome, email, senha, papel, escola_nome")
                continue
            
            # Validate papel
            if papel not in ['aluno', 'professor']:
                errors.append(f"Linha {idx+2}: Papel deve ser 'aluno' ou 'professor'")
                continue
            
            # Validate password
            if len(senha) < 6:
                errors.append(f"Linha {idx+2}: Senha deve ter no mínimo 6 caracteres")
                continue
            
            # Check email unique
            existing = db.query(models.User).filter(models.User.email == email).first()
            if existing:
                errors.append(f"Linha {idx+2}: Email '{email}' já cadastrado")
                continue
            
            # Find school
            escola = db.query(models.Escola).filter(models.Escola.nome == escola_nome).first()
            if not escola:
                errors.append(f"Linha {idx+2}: Escola '{escola_nome}' não encontrada")
                continue
            
            # Validate aluno requirements
            if papel == 'aluno' and not serie_nome:
                errors.append(f"Linha {idx+2}: Série obrigatória para alunos")
                continue
            
            # Validate professor requirements
            if papel == 'professor' and not disciplina:
                errors.append(f"Linha {idx+2}: Disciplina obrigatória para professores")
                continue
            
            # Find or create serie for students
            serie_id = None
            if papel == 'aluno':
                serie = db.query(models.Serie).filter(
                    models.Serie.nome == serie_nome,
                    models.Serie.escola_id == escola.id
                ).first()
                
                if not serie:
                    # Create serie automatically
                    serie = models.Serie(nome=serie_nome, escola_id=escola.id)
                    db.add(serie)
                    db.commit()
                    db.refresh(serie)
                    logger.info(f"Série criada automaticamente: {serie_nome}")
                
                serie_id = serie.id
            
            # Create user
            user = models.User(
                email=email,
                nome=nome,
                senha_hash=auth.get_password_hash(senha),
                papel=papel,
                escola_id=escola.id,
                serie_id=serie_id,
                disciplina=disciplina if papel == 'professor' else None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created.append(f"{nome} ({papel})")
            logger.info(f"Usuário criado via CSV: {email} - {papel}")
            
        except Exception as e:
            db.rollback()
            errors.append(f"Linha {idx+2}: {str(e)}")
            logger.error(f"Error processing usuario CSV row {idx}: {e}")
    
    return {
        "success": len(created),
        "errors": len(errors),
        "created": created,
        "error_details": errors
    }
