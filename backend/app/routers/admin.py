from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import pandas as pd
from io import BytesIO
import os
import uuid
from PIL import Image

from ..database import get_db
from .. import models, schemas, auth, csv_handler

router = APIRouter(
    tags=["admin"]
)

logger = logging.getLogger(__name__)

# ==================== CSV ENDPOINTS ====================

@router.post("/admin/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    tipo: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Upload CSV para cadastro em massa.
    Tipos aceitos: escolas, gestores, usuarios
    """
    if current_user.papel not in ['admin', 'gestor']:
        raise HTTPException(status_code=403, detail="Apenas administradores e gestores podem fazer upload de CSV")

    # Gestores só podem importar usuarios
    if current_user.papel == 'gestor' and tipo != 'usuarios':
        raise HTTPException(
            status_code=403, 
            detail="Gestores podem importar apenas 'usuarios' (alunos e professores)"
        )
    
    # Validar que gestor tem escola
    if current_user.papel == 'gestor' and not current_user.escola_id:
        raise HTTPException(status_code=400, detail="Gestor não está associado a uma escola")
    
    # Validate type
    valid_tipos = ["escolas", "gestores", "usuarios"]
    if tipo not in valid_tipos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Use: {', '.join(valid_tipos)}")
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .csv")
    
    try:
        # Read CSV
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))
        
        logger.info(f"Processing CSV upload: type={tipo}, rows={len(df)}, user={current_user.email}")
        
        # Process based on type
        if tipo == "escolas":
            result = csv_handler.process_escolas_csv(df, db)
        elif tipo == "gestores":
            result = csv_handler.process_gestores_csv(df, db)
        elif tipo == "usuarios":
            # Para gestores, passar escola_id_filter
            if current_user.papel == 'gestor':
                result = csv_handler.process_usuarios_csv(df, db, escola_id_filter=current_user.escola_id)
            else:
                result = csv_handler.process_usuarios_csv(df, db)
        
        logger.info(f"CSV processed: success={result['success']}, errors={result['errors']}")
        return result
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Arquivo CSV está vazio")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler CSV: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar CSV: {str(e)}")

@router.post("/users/import")
async def import_users(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Endpoint legado para importação de usuários (usado pelo frontend).
    """
    if current_user.papel not in ['admin', 'gestor']:
        raise HTTPException(status_code=403, detail="Apenas administradores e gestores podem importar usuários")
    
    # Validar que gestor tem escola
    if current_user.papel == 'gestor' and not current_user.escola_id:
        raise HTTPException(status_code=400, detail="Gestor não está associado a uma escola")
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .csv")
    
    try:
        # Read CSV
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))
        
        logger.info(f"Processing User Import: rows={len(df)}, user={current_user.email}")
        
        # Process users
        if current_user.papel == 'gestor':
            result = csv_handler.process_usuarios_csv(df, db, escola_id_filter=current_user.escola_id)
        else:
            result = csv_handler.process_usuarios_csv(df, db)
        
        logger.info(f"CSV processed: success={result['success']}, errors={result['errors']}")
        
        # Format result to match what frontend expects
        # Frontend expects: { imported: number, errors: list }
        # csv_handler returns: { success: int, errors: list, total: int }
        
        return {
            "imported": result['success'],
            "errors": result['error_details'],
            "total": len(df)
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Arquivo CSV está vazio")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler CSV: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao processar CSV: {str(e)}")

@router.get("/admin/csv-template/{tipo}")
def download_csv_template(
    tipo: str,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Download template CSV para upload"""
    if current_user.papel not in ['admin', 'gestor']:
        raise HTTPException(status_code=403, detail="Apenas administradores e gestores podem baixar templates")

    # Gestores só podem baixar template de usuarios
    if current_user.papel == 'gestor' and tipo != 'usuarios':
        raise HTTPException(
            status_code=403, 
            detail="Gestores podem baixar apenas o template de 'usuarios'"
        )
    
    templates = {
        "escolas": "nome\nEscola Exemplo\n",
        "gestores": "nome,email,senha,escola_nome\nCarlos Silva,carlos@escola.com,senha123,Escola Exemplo\n",
        "usuarios": "nome,email,senha,papel,serie,disciplina,escola_nome\nJoão Aluno,joao@aluno.com,senha123,aluno,5º Ano,,Escola Exemplo\nProf. Ana,ana@prof.com,profsenha,professor,,,Matemática,Escola Exemplo\n"
    }

    # Template especial para gestores (sem coluna escola_nome)
    if current_user.papel == 'gestor' and tipo == 'usuarios':
        templates["usuarios"] = (
            "nome,email,senha,papel,serie,disciplina\n"
            "João Aluno,joao@aluno.com,senha123,aluno,5º Ano,\n"
            "Prof. Ana,ana@prof.com,profsenha,professor,,Matemática\n"
        )
    
    if tipo not in templates:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return Response(
        content=templates[tipo],
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={tipo}_template.csv"}
    )

# ==================== USER MANAGEMENT ====================

@router.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Criar novo usuário."""
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Se quem está criando é gestor, forçar a escola do gestor
    escola_id_to_use = user.escola_id
    if current_user.papel == 'gestor':
        escola_id_to_use = current_user.escola_id

    qr_token = str(uuid.uuid4())

    db_user = models.User(
        email=user.email, 
        nome=user.nome, 
        senha_hash=auth.get_password_hash(user.senha),
        papel=user.papel,
        serie_id=user.serie_id,
        disciplina=user.disciplina,
        escola_id=escola_id_to_use,
        qr_token=qr_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created: {user.email} ({user.papel})")
    return db_user

@router.get("/users/", response_model=list[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    query = db.query(models.User)
    
    # Filter by school for gestor users
    if current_user.papel == 'gestor' and current_user.escola_id:
        query = query.filter(models.User.escola_id == current_user.escola_id)
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "nome": current_user.nome,
        "papel": current_user.papel,
        "serie_id": current_user.serie_id,
        "serie_nome": current_user.serie_nome,
        "disciplina": current_user.disciplina,
        "escola_id": current_user.escola_id,
        "pontos": current_user.pontos,
        "moedas": current_user.moedas,
        "xp": current_user.xp,
        "nivel": current_user.nivel,
        "streak_count": current_user.streak_count,
        "avatar_url": current_user.avatar_url,
        "bio": current_user.bio,
        "interesses": current_user.interesses,
        "escola_nome": current_user.escola.nome if current_user.escola else None,
        "qr_token": current_user.qr_token
    }
    return user_dict

@router.get("/users/{user_id}/profile")
def get_user_profile(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get full profile for a specific user."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    # Basic info
    profile_data = {
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "papel": user.papel,
        "serie": user.serie_nome,
        "nivel": user.nivel,
        "xp": user.xp,
        "moedas": user.moedas,
        "bio": user.bio,
        "interesses": user.interesses,
        "avatar_url": user.avatar_url,
        "escola_nome": user.escola.nome if user.escola else None,
        "joined_at": user.criado_em
    }
    
    # Clan info
    clan_member = db.query(models.ClanMember).filter(models.ClanMember.user_id == user.id).first()
    if clan_member:
        profile_data["clan"] = {
            "id": clan_member.clan.id,
            "nome": clan_member.clan.nome,
            "papel": clan_member.papel
        }
    else:
        profile_data["clan"] = None
        
    # Completed Missions (Last 5)
    completed_missions = db.query(models.MissaoConcluida).filter(
        models.MissaoConcluida.aluno_id == user.id,
        models.MissaoConcluida.validada == True
    ).order_by(models.MissaoConcluida.data_validacao.desc()).limit(5).all()
    
    profile_data["missoes_concluidas"] = [
        {
            "titulo": cm.missao.titulo,
            "pontos": cm.missao.pontos,
            "data": cm.data_validacao
        } for cm in completed_missions
    ]
    
    # Mural Posts (Last 5)
    mural_posts = db.query(models.MuralPost).filter(models.MuralPost.user_id == user.id).order_by(models.MuralPost.data_criacao.desc()).limit(5).all()
    
    profile_data["posts"] = [
        {
            "id": post.id,
            "conteudo": post.texto,
            "likes": len(post.likes) if post.likes else 0,
            "data": post.data_criacao
        } for post in mural_posts
    ]
    
    return profile_data

@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Update user information."""
    if current_user.id != user_id and current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Gestor can only edit users from their school
    if current_user.papel == 'gestor' and db_user.escola_id != current_user.escola_id:
        raise HTTPException(status_code=403, detail="Você só pode editar usuários da sua escola")
    
    # Update fields based on what was provided
    update_data = user_update.dict(exclude_unset=True)
    
    # Fields that any user can update
    if 'nome' in update_data:
        db_user.nome = update_data['nome']
    if 'email' in update_data:
        db_user.email = update_data['email']
    if 'bio' in update_data:
        db_user.bio = update_data['bio']
    if 'interesses' in update_data:
        db_user.interesses = update_data['interesses']
    
    # Sensitive fields can only be changed by admin/gestor
    if current_user.papel in ['gestor', 'admin']:
        if 'papel' in update_data:
            db_user.papel = update_data['papel']
        if 'serie_id' in update_data:
            db_user.serie_id = update_data['serie_id']
        if 'disciplina' in update_data:
            db_user.disciplina = update_data['disciplina']
        if 'escola_id' in update_data:
            db_user.escola_id = update_data['escola_id']
    
    # Update password if provided
    if user_update.senha:
        db_user.senha_hash = auth.get_password_hash(user_update.senha)
    
    db.commit()
    db.refresh(db_user)
    logger.info(f"User updated: {db_user.email} by {current_user.email}")
    return db_user

@router.delete("/users/all")
def delete_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Delete ALL students (Danger Zone)."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    query = db.query(models.User).filter(models.User.papel == 'aluno')
    
    # Gestor can only delete students from their school
    if current_user.papel == 'gestor':
        if not current_user.escola_id:
            raise HTTPException(status_code=400, detail="Gestor sem escola vinculada")
        query = query.filter(models.User.escola_id == current_user.escola_id)
    
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    
    logger.warning(f"ALL STUDENTS DELETED by {current_user.email}. Count: {deleted_count}")
    return {"message": "Todos os alunos foram deletados", "deleted": deleted_count}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Delete a user."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Gestor can only delete users from their school
    if current_user.papel == 'gestor' and db_user.escola_id != current_user.escola_id:
        raise HTTPException(status_code=403, detail="Você só pode deletar usuários da sua escola")
    
    # Prevent deleting yourself
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Você não pode deletar a si mesmo")
    
    db.delete(db_user)
    db.commit()
    logger.info(f"User deleted: {db_user.email} by {current_user.email}")
    return {"message": "Usuário deletado com sucesso"}

@router.post("/admin/gestor", response_model=schemas.UserResponse)
def create_gestor(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar gestores")
        
    if user.papel != 'gestor':
        raise HTTPException(status_code=400, detail="O papel deve ser 'gestor'")
        
    if not user.escola_id:
        raise HTTPException(status_code=400, detail="Gestor deve estar vinculado a uma escola")
        
    return create_user(user, db, current_user)

@router.put("/users/me/profile", response_model=schemas.UserResponse)
def update_profile(bio: str = None, interesses: str = None, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    try:
        # Re-query user to ensure it's attached to the current session
        user_db = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not user_db:
            raise HTTPException(status_code=404, detail="User not found")
            
        if bio is not None:
            user_db.bio = bio
        if interesses is not None:
            user_db.interesses = interesses
        db.commit()
        db.refresh(user_db)
        logger.info(f"Profile updated: {user_db.email}")
        return user_db
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar perfil: {str(e)}")

@router.get("/users/me/inventory")
def get_inventory(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    inventario = db.query(models.UserItem).filter(models.UserItem.user_id == current_user.id).all()
    return inventario

# ==================== AVATAR MANAGEMENT ====================

async def process_avatar_image(file: UploadFile, max_size_mb: int = 5, max_dim: int = 800) -> tuple[bytes, str]:
    """Validates, resizes and optimizes an avatar image."""
    # 1. Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail=f"Arquivo deve ser uma imagem. Tipo recebido: {file.content_type}")
    
    # 2. Validate file extension
    allowed_extensions = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
    file_extension = file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else None
    
    if not file_extension or file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Extensão não permitida. Use: {', '.join(allowed_extensions)}"
        )
    
    # 3. Read and validate file size
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Imagem deve ter no máximo {max_size_mb}MB")
    
    # 4. Open and resize image
    try:
        image = Image.open(BytesIO(contents))
        
        # Convert RGBA to RGB if needed
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize
        image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = BytesIO()
        save_format = 'JPEG' if file_extension in ['jpg', 'jpeg'] else file_extension.upper()
        
        if save_format == 'JPEG':
            image.save(output, format=save_format, quality=85, optimize=True)
        else:
            image.save(output, format=save_format, optimize=True)
        
        return output.getvalue(), file_extension
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar imagem: {str(e)}")

def save_avatar_for_user(user: models.User, contents: bytes, extension: str, db: Session):
    """Saves avatar file and updates user record."""
    # Create uploads directory
    upload_dir = "media/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    safe_filename = f"avatar_{user.id}_{int(datetime.now().timestamp())}.{extension}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    # Delete old avatar
    if user.avatar_url:
        old_file_path = user.avatar_url.lstrip('/')
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
                logger.info(f"Old avatar deleted: {old_file_path}")
            except Exception as e:
                logger.warning(f"Could not delete old avatar: {e}")
    
    # Save new file
    with open(file_path, 'wb') as f:
        f.write(contents)
    
    # Update user
    user.avatar_url = f"/{file_path.replace(os.sep, '/')}"
    db.commit()
    db.refresh(user)
    logger.info(f"Avatar saved for user {user.email}: {user.avatar_url}")
    return user

@router.post("/users/me/avatar", response_model=schemas.UserResponse)
async def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Upload user avatar image with validation, resizing, and cleanup."""
    try:
        logger.info(f"Avatar upload started for user {current_user.email}")
        
        # Process image
        contents, extension = await process_avatar_image(file)
        
        # Save and update user
        updated_user = save_avatar_for_user(current_user, contents, extension, db)
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao salvar imagem: {str(e)}")

@router.post("/users/{user_id}/avatar", response_model=schemas.UserResponse)
async def upload_user_avatar(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Upload avatar for a specific user - only owner or admin can upload."""
    try:
        # Check permissions: only owner or admin
        if current_user.id != user_id and current_user.papel != 'admin':
            raise HTTPException(status_code=403, detail="Você não tem permissão para alterar o avatar deste usuário")
        
        logger.info(f"Avatar upload started for user ID {user_id} by {current_user.email}")
        
        # Get target user
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Process image
        contents, extension = await process_avatar_image(file)
        
        # Save and update user
        updated_user = save_avatar_for_user(db_user, contents, extension, db)
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao salvar imagem: {str(e)}")

# ==================== SCHOOL & SERIES ====================

@router.post("/escolas/", response_model=schemas.EscolaResponse)
def create_escola(escola: schemas.EscolaCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar escolas")
        
    db_escola = models.Escola(nome=escola.nome)
    db.add(db_escola)
    db.commit()
    db.refresh(db_escola)
    return db_escola

@router.get("/escolas/", response_model=list[schemas.EscolaResponse])
def read_escolas(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem ver todas as escolas")
    return db.query(models.Escola).all()

@router.delete("/escolas/{escola_id}")
def delete_escola(escola_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir escolas")
    
    escola = db.query(models.Escola).filter(models.Escola.id == escola_id).first()
    if not escola:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
        
    db.delete(escola)
    db.commit()
    return {"message": "Escola excluída com sucesso"}

@router.get("/series/", response_model=list[schemas.SerieResponse])
def get_series(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get all series for the manager's school."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas gestores podem acessar séries")
    
    if current_user.papel == 'admin':
        # Admin can see all series
        return db.query(models.Serie).all()
    
    # Manager sees only their school's series
    return db.query(models.Serie).filter(models.Serie.escola_id == current_user.escola_id).all()

@router.post("/series/", response_model=schemas.SerieResponse)
def create_serie(serie: schemas.SerieCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Create a new serie for the manager's school."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas gestores podem criar séries")
    
    if not current_user.escola_id:
        raise HTTPException(status_code=400, detail="Usuário não está associado a uma escola")
    
    # Check if serie with same name already exists in this school
    existing = db.query(models.Serie).filter(
        models.Serie.nome == serie.nome,
        models.Serie.escola_id == current_user.escola_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Série já existe nesta escola")
    
    db_serie = models.Serie(**serie.dict(), escola_id=current_user.escola_id)
    db.add(db_serie)
    db.commit()
    db.refresh(db_serie)
    logger.info(f"Serie created: {serie.nome} by {current_user.nome}")
    return db_serie

@router.put("/series/{serie_id}", response_model=schemas.SerieResponse)
def update_serie(serie_id: int, serie: schemas.SerieUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Update a serie."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas gestores podem editar séries")
    
    db_serie = db.query(models.Serie).filter(models.Serie.id == serie_id).first()
    if not db_serie:
        raise HTTPException(status_code=404, detail="Série não encontrada")
    
    # Verify the serie belongs to the manager's school
    if current_user.papel == 'gestor' and db_serie.escola_id != current_user.escola_id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para editar esta série")
    
    # Check if new name conflicts with existing serie in the same school
    if serie.nome != db_serie.nome:
        existing = db.query(models.Serie).filter(
            models.Serie.nome == serie.nome,
            models.Serie.escola_id == db_serie.escola_id,
            models.Serie.id != serie_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Já existe uma série com este nome nesta escola")
    
    db_serie.nome = serie.nome
    db.commit()
    db.refresh(db_serie)
    logger.info(f"Serie updated: {serie.nome} by {current_user.nome}")
    return db_serie

@router.delete("/series/{serie_id}")
def delete_serie(serie_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Delete a serie."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas gestores podem excluir séries")
    
    db_serie = db.query(models.Serie).filter(models.Serie.id == serie_id).first()
    if not db_serie:
        raise HTTPException(status_code=404, detail="Série não encontrada")
    
    # Verify the serie belongs to the manager's school
    if current_user.papel == 'gestor' and db_serie.escola_id != current_user.escola_id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para excluir esta série")
    
    # Check if there are users associated with this serie
    users_count = db.query(models.User).filter(models.User.serie_id == serie_id).count()
    if users_count > 0:
        raise HTTPException(status_code=400, detail=f"Não é possível excluir esta série pois existem {users_count} usuários associados a ela")
    
    db.delete(db_serie)
    db.commit()
    logger.info(f"Serie deleted: {db_serie.nome} by {current_user.nome}")
    return {"message": "Série excluída com sucesso"}

# ==================== REPORTS ENDPOINTS ====================

@router.get("/reports/stats")
def get_reports_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get statistics for manager/admin dashboard."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    total_alunos = db.query(models.User).filter(models.User.papel == 'aluno', models.User.escola_id == current_user.escola_id).count()
    total_missoes = db.query(models.Missao).filter(models.Missao.criador_id == current_user.id).count()
    
    # Top 3 Alunos
    top_alunos = db.query(models.User).filter(
        models.User.papel == 'aluno',
        models.User.escola_id == current_user.escola_id
    ).order_by(models.User.xp.desc()).limit(3).all()
    
    top_alunos_data = [
        {"nome": u.nome, "xp": u.xp, "nivel": u.nivel} for u in top_alunos
    ]
    
    # Média de XP
    all_students = db.query(models.User).filter(models.User.papel == 'aluno', models.User.escola_id == current_user.escola_id).all()
    avg_xp = sum([u.xp for u in all_students]) / len(all_students) if all_students else 0
    
    return {
        "total_alunos": total_alunos,
        "total_missoes": total_missoes,
        "media_xp": int(avg_xp),
        "top_alunos": top_alunos_data
    }

@router.get("/reports/top_professors")
def get_top_professors(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get professors with most completed missions."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    professores = db.query(models.User).filter(
        models.User.papel == 'professor', 
        models.User.escola_id == current_user.escola_id
    ).all()
    
    result = []
    for prof in professores:
        # Count completed and validated missions for this professor
        count = db.query(models.MissaoConcluida).join(models.Missao).filter(
            models.Missao.criador_id == prof.id,
            models.MissaoConcluida.validada == True
        ).count()
        result.append({"nome": prof.nome, "missoes_concluidas": count})
        
    # Sort by completed missions
    result.sort(key=lambda x: x['missoes_concluidas'], reverse=True)
    
    return result[:5]

@router.get("/reports/top_schools")
def get_top_schools(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get top schools by total student XP."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    escolas = db.query(models.Escola).all()
    
    result = []
    for escola in escolas:
        # Sum XP of all students in this school
        total_xp = db.query(func.sum(models.User.xp)).filter(
            models.User.escola_id == escola.id,
            models.User.papel == 'aluno'
        ).scalar() or 0
        
        result.append({
            "nome": escola.nome,
            "total_xp": int(total_xp)
        })
    
    # Sort by total XP
    result.sort(key=lambda x: x['total_xp'], reverse=True)
    
    return result[:5]

@router.get("/reports/participation")
def get_participation_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get participation stats by serie (average XP)."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    alunos = db.query(models.User).filter(
        models.User.papel == 'aluno',
        models.User.escola_id == current_user.escola_id
    ).all()
    
    stats = {}
    for aluno in alunos:
        serie = aluno.serie_nome or "Sem Série"
        if serie not in stats:
            stats[serie] = {"total_xp": 0, "alunos": 0}
        stats[serie]["total_xp"] += aluno.xp
        stats[serie]["alunos"] += 1
        
    return [{"serie": k, "media_xp": v["total_xp"] // v["alunos"] if v["alunos"] > 0 else 0} for k, v in stats.items()]

# ==================== QR CODE ENDPOINTS ====================

@router.get("/users/me/qrcode")
def get_my_qrcode(current_user: models.User = Depends(auth.get_current_user)):
    """Generate QR Code for current user."""
    import qrcode
    import base64
    from io import BytesIO
    
    # QR Code data (can be a validation token or ID)
    data = f"schoolquest:user:{current_user.id}:{current_user.qr_token}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return {"qrcode_base64": f"data:image/png;base64,{img_str}"}

class QRCodeRequest(BaseModel):
    qr_data: str

@router.post("/users/validate_qrcode")
def validate_qrcode(request: QRCodeRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Validate QR Code and return student data."""
    if current_user.papel not in ['professor', 'gestor']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Format: schoolquest:user:{id}:{qr_token}
    try:
        parts = request.qr_data.split(":")
        if len(parts) != 4 or parts[0] != "schoolquest" or parts[1] != "user":
            raise HTTPException(status_code=400, detail="QR Code inválido")
            
        user_id = int(parts[2])
        qr_token = parts[3]
        
        user = db.query(models.User).filter(models.User.id == user_id, models.User.qr_token == qr_token).first()
        if not user:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
            
        return {
            "id": user.id,
            "nome": user.nome,
            "serie": user.serie_nome,
            "nivel": user.nivel,
            "xp": user.xp,
            "avatar_url": user.avatar_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Erro ao processar QR Code")

# ==================== USER SEARCH ====================

@router.get("/users/search", response_model=list[schemas.UserResponse])
def search_users(q: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Search for students from the same school who are not in a clan."""
    if not q:
        return []
        
    # Search students from same school containing 'q' in name or email
    users = db.query(models.User).filter(
        models.User.escola_id == current_user.escola_id,
        models.User.papel == 'aluno'
    ).all()
    
    # Filter in python for case-insensitive search
    q_lower = q.lower()
    users = [u for u in users if q_lower in u.nome.lower() or q_lower in u.email.lower()]
    
    # Filter out users who already have a clan
    available_users = []
    for user in users:
        in_clan = db.query(models.ClanMember).filter(models.ClanMember.user_id == user.id).first()
        if not in_clan:
            available_users.append(user)
            
    return available_users

# ==================== RANKING ====================

@router.get("/ranking")
def get_ranking(limit: int = 10, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get ranking of students by XP."""
    ranking = db.query(models.User).filter(
        models.User.papel == 'aluno',
        models.User.escola_id == current_user.escola_id
    ).order_by(models.User.xp.desc()).limit(limit).all()
    
    return [
        {
            "id": user.id,
            "nome": user.nome,
            "nivel": user.nivel,
            "xp": user.xp,
            "serie": user.serie_nome
        } for user in ranking
    ]

# ==================== FIX QR TOKENS ====================

@router.post("/users/fix-qr-tokens")
def fix_qr_tokens(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Generate QR tokens for users who don't have one (admin/manager only)."""
    if current_user.papel not in ['admin', 'gestor']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    import uuid
    
    # Get users without QR token
    users_without_token = db.query(models.User).filter(
        (models.User.qr_token == None) | (models.User.qr_token == '')
    ).all()
    
    count = 0
    for user in users_without_token:
        user.qr_token = str(uuid.uuid4())
        count += 1
    
    db.commit()
    
    return {
        "message": f"{count} usuários atualizados com QR tokens",
        "count": count
    }
