from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
from . import models, schemas, database, auth
from .routers import shop, mural
from .config import settings
import os
import qrcode
import io
import csv
from io import BytesIO
import base64
from fastapi.staticfiles import StaticFiles

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(title="SchoolQuest API", version="1.0.0")

# CORS Middleware - DEVE VIR ANTES DE TUDO
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar tabelas
models.Base.metadata.create_all(bind=database.engine)

# Routers
app.include_router(shop.router)
app.include_router(mural.router)

# Static files
app.mount("/media", StaticFiles(directory="media"), name="media")
# Mount uploads directory for avatars
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Create default users on startup."""
    db = database.SessionLocal()
    try:
        # Check for admin user
        admin = db.query(models.User).filter(models.User.email == "admin@test.com").first()
        if not admin:
            logger.info("Creating default admin user...")
            admin_user = models.User(
                email="admin@test.com",
                nome="Administrador",
                senha_hash=auth.get_password_hash("admin123"),
                papel="admin",
                pontos=1000,
                xp=1000,
                nivel=10
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created: admin@test.com / admin123")
        else:
            logger.info("Admin user already exists.")
    except Exception as e:
        logger.error(f"Error creating default users: {e}")
    finally:
        db.close()


# Global Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handler para HTTPException com logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handler para erros de validação."""
    logger.error(f"Validation error: {exc.errors()} - Path: {request.url.path}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Dados inválidos", "errors": exc.errors()}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Handler global para exceções não tratadas."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )

# Dependência
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    """Endpoint raiz da API."""
    logger.info("Root endpoint accessed")
    return {
        "message": "SchoolQuest API",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs"
    }

@app.post("/auth/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Endpoint de autenticação - retorna JWT token."""
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.senha_hash):
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login: {user.email} (ID: {user.id})")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Criar novo usuário."""
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Se quem está criando é gestor, forçar a escola do gestor
    escola_id_to_use = user.escola_id
    if current_user.papel == 'gestor':
        escola_id_to_use = current_user.escola_id

    db_user = models.User(
        email=user.email, 
        nome=user.nome, 
        senha_hash=auth.get_password_hash(user.senha),
        papel=user.papel,
        serie_id=user.serie_id,
        disciplina=user.disciplina,
        escola_id=escola_id_to_use
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created: {user.email} ({user.papel})")
    return db_user

@app.post("/escolas/", response_model=schemas.EscolaResponse)
def create_escola(escola: schemas.EscolaCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar escolas")
        
    db_escola = models.Escola(nome=escola.nome)
    db.add(db_escola)
    db.commit()
    db.refresh(db_escola)
    return db_escola

@app.get("/escolas/", response_model=list[schemas.EscolaResponse])
def read_escolas(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem ver todas as escolas")
    return db.query(models.Escola).all()

@app.delete("/escolas/{escola_id}")
def delete_escola(escola_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem excluir escolas")
    
    escola = db.query(models.Escola).filter(models.Escola.id == escola_id).first()
    if not escola:
        raise HTTPException(status_code=404, detail="Escola não encontrada")
        
    db.delete(escola)
    db.commit()
    return {"message": "Escola excluída com sucesso"}

# Series Management Endpoints
@app.get("/series/", response_model=list[schemas.SerieResponse])
def get_series(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Get all series for the manager's school."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas gestores podem acessar séries")
    
    if current_user.papel == 'admin':
        # Admin can see all series
        return db.query(models.Serie).all()
    
    # Manager sees only their school's series
    return db.query(models.Serie).filter(models.Serie.escola_id == current_user.escola_id).all()

@app.post("/series/", response_model=schemas.SerieResponse)
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

@app.put("/series/{serie_id}", response_model=schemas.SerieResponse)
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

@app.delete("/series/{serie_id}")
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


@app.post("/admin/gestor", response_model=schemas.UserResponse)
def create_gestor(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar gestores")
        
    if user.papel != 'gestor':
        raise HTTPException(status_code=400, detail="O papel deve ser 'gestor'")
        
    if not user.escola_id:
        raise HTTPException(status_code=400, detail="Gestor deve estar vinculado a uma escola")
        
    return create_user(user, db, current_user)

@app.get("/users/me", response_model=schemas.UserResponse)
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
        "escola_nome": current_user.escola.nome if current_user.escola else None
    }
    return user_dict

@app.post("/users/me/avatar", response_model=schemas.UserResponse)
async def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Upload user avatar image."""
    try:
        logger.info(f"Avatar upload started for user {current_user.email}, file: {file.filename}, content_type: {file.content_type}")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"Arquivo deve ser uma imagem. Tipo recebido: {file.content_type}")
        
        # Validate file size (5MB max)
        contents = await file.read()
        file_size = len(contents)
        logger.info(f"File size: {file_size} bytes")
        
        if file_size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Imagem deve ter no máximo 5MB")
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/avatars"
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"Upload directory ensured: {upload_dir}")
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if file.filename and '.' in file.filename else 'jpg'
        safe_filename = f"avatar_{current_user.id}_{int(datetime.now().timestamp())}.{file_extension}"
        file_path = os.path.join(upload_dir, safe_filename)
        logger.info(f"Saving to: {file_path}")
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        logger.info(f"File saved successfully: {file_path}")
        
        # Re-query user in current session to avoid detached instance error
        db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        # Update user avatar URL
        avatar_url = f"/{file_path.replace(os.sep, '/')}"
        db_user.avatar_url = avatar_url
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Avatar uploaded successfully for user {db_user.email}: {avatar_url}")
        
        # Return updated user data
        user_dict = {
            "id": db_user.id,
            "email": db_user.email,
            "nome": db_user.nome,
            "papel": db_user.papel,
            "serie": db_user.serie,
            "disciplina": db_user.disciplina,
            "escola_id": db_user.escola_id,
            "pontos": db_user.pontos,
            "moedas": db_user.moedas,
            "xp": db_user.xp,
            "nivel": db_user.nivel,
            "streak_count": db_user.streak_count,
            "avatar_url": db_user.avatar_url,
            "bio": db_user.bio,
            "interesses": db_user.interesses,
            "escola_nome": db_user.escola.nome if db_user.escola else None
        }
        return user_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao salvar imagem: {str(e)}")

@app.get("/users/", response_model=list[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    query = db.query(models.User)
    
    # Filter by school for gestor users
    if current_user.papel == 'gestor' and current_user.escola_id:
        query = query.filter(models.User.escola_id == current_user.escola_id)
    
    users = query.offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}/profile")
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
    mural_posts = db.query(models.MuralPost).filter(models.MuralPost.user_id == user.id).order_by(models.MuralPost.criado_em.desc()).limit(5).all()
    
    profile_data["posts"] = [
        {
            "id": post.id,
            "conteudo": post.conteudo,
            "likes": post.likes,
            "data": post.data_criacao
        } for post in mural_posts
    ]
    
    return profile_data

@app.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_update: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Update user information."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Gestor can only edit users from their school
    if current_user.papel == 'gestor' and db_user.escola_id != current_user.escola_id:
        raise HTTPException(status_code=403, detail="Você só pode editar usuários da sua escola")
    
    # Update fields
    db_user.nome = user_update.nome
    db_user.email = user_update.email
    db_user.papel = user_update.papel
    db_user.serie_id = user_update.serie_id
    db_user.disciplina = user_update.disciplina
    db_user.escola_id = user_update.escola_id
    
    # Update password if provided
    if user_update.senha:
        db_user.senha_hash = auth.get_password_hash(user_update.senha)
    
    db.commit()
    db.refresh(db_user)
    logger.info(f"User updated: {db_user.email} by {current_user.email}")
    return db_user

@app.delete("/users/{user_id}")
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

@app.post("/missoes/", response_model=schemas.MissaoResponse)
def create_missao(missao: schemas.MissaoCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Criar nova missão."""
    db_missao = models.Missao(**missao.dict(), criador_id=current_user.id)
    db.add(db_missao)
    db.commit()
    db.refresh(db_missao)
    logger.info(f"Mission created: {missao.titulo} by {current_user.nome}")
    return db_missao

@app.delete("/missoes/{missao_id}")
def delete_missao(missao_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Deletar uma missão (apenas o criador ou gestor)."""
    missao = db.query(models.Missao).filter(models.Missao.id == missao_id).first()
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    
    if current_user.papel != 'admin' and current_user.papel != 'gestor' and missao.criador_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você não tem permissão para excluir esta missão")
        
    db.delete(missao)
    db.commit()
    return {"message": "Missão excluída com sucesso"}

@app.post("/missoes/atribuir", response_model=schemas.MissaoAtribuidaResponse)
def atribuir_missao(
    atribuicao: schemas.MissaoAtribuidaCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.papel not in ['professor', 'gestor']:
        raise HTTPException(status_code=403, detail="Apenas professores podem atribuir missões")
    
    missao = db.query(models.Missao).filter(models.Missao.id == atribuicao.missao_id).first()
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    
    if missao.criador_id != current_user.id and current_user.papel != 'gestor':
        raise HTTPException(status_code=403, detail="Você só pode atribuir suas próprias missões")

    # Check if already assigned
    existing = db.query(models.MissaoAtribuida).filter(
        models.MissaoAtribuida.missao_id == atribuicao.missao_id,
        models.MissaoAtribuida.aluno_id == atribuicao.aluno_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Missão já atribuída a este aluno")

    db_atribuicao = models.MissaoAtribuida(
        missao_id=atribuicao.missao_id,
        aluno_id=atribuicao.aluno_id,
        status="pendente"
    )
    db.add(db_atribuicao)
    db.commit()
    db.refresh(db_atribuicao)
    
    # Manually populate for response
    db_atribuicao.aluno_nome = db_atribuicao.aluno.nome
    
    return db_atribuicao

@app.get("/missoes/recebidas", response_model=List[schemas.MissaoAtribuidaResponse])
def get_missoes_recebidas(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    missoes = db.query(models.MissaoAtribuida).filter(
        models.MissaoAtribuida.aluno_id == current_user.id,
        models.MissaoAtribuida.status == "pendente"
    ).all()
    
    for m in missoes:
        m.aluno_nome = current_user.nome
        
    return missoes

@app.post("/missoes/atribuidas/{id}/aceitar")
def aceitar_missao(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    atribuicao = db.query(models.MissaoAtribuida).filter(models.MissaoAtribuida.id == id).first()
    if not atribuicao:
        raise HTTPException(status_code=404, detail="Atribuição não encontrada")
    
    if atribuicao.aluno_id != current_user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")
        
    atribuicao.status = "aceita"
    atribuicao.data_resposta = datetime.utcnow()
    db.commit()
    return {"message": "Missão aceita"}

@app.post("/missoes/atribuidas/{id}/recusar")
def recusar_missao(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    atribuicao = db.query(models.MissaoAtribuida).filter(models.MissaoAtribuida.id == id).first()
    if not atribuicao:
        raise HTTPException(status_code=404, detail="Atribuição não encontrada")
    
    if atribuicao.aluno_id != current_user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")
        
    atribuicao.status = "recusada"
    atribuicao.data_resposta = datetime.utcnow()
    db.commit()
    return {"message": "Missão recusada"}

@app.get("/missoes/professor/atribuidas", response_model=List[schemas.MissaoAtribuidaResponse])
def get_professor_atribuidas(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.papel not in ['professor', 'gestor']:
        raise HTTPException(status_code=403, detail="Apenas professores podem ver atribuições")

    results = db.query(models.MissaoAtribuida).join(models.Missao).filter(
        models.Missao.criador_id == current_user.id
    ).all()
    
    for res in results:
        res.aluno_nome = res.aluno.nome if res.aluno else "Desconhecido"
        
    return results

@app.get("/missoes/professor/concluidas")
def get_professor_concluidas(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.papel not in ['professor', 'gestor']:
        raise HTTPException(status_code=403, detail="Apenas professores podem ver missões concluídas")

    conclusoes = db.query(models.MissaoConcluida).join(models.Missao).filter(
        models.Missao.criador_id == current_user.id,
        models.MissaoConcluida.validada == True
    ).all()
    
    resultado = []
    for sub in conclusoes:
        resultado.append({
            "id": sub.id,
            "aluno_nome": sub.aluno.nome,
            "aluno_serie": sub.aluno.serie_nome,
            "missao_titulo": sub.missao.titulo,
            "data_solicitacao": sub.data_solicitacao,
            "data_validacao": sub.data_validacao
        })
    return resultado

@app.get("/missoes/", response_model=list[schemas.MissaoResponse])
def read_missoes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    missoes = db.query(models.Missao).offset(skip).limit(limit).all()
    
    # Calcular status para o usuário atual
    resultado = []
    for missao in missoes:
        status_missao = "disponivel"
        conclusao = db.query(models.MissaoConcluida).filter_by(
            missao_id=missao.id, 
            aluno_id=current_user.id
        ).first()
        
        if conclusao:
            if conclusao.validada:
                status_missao = "aprovada"
            else:
                status_missao = "pendente"
        
        missao_resp = schemas.MissaoResponse(
            **missao.__dict__,
            status=status_missao
        )
        resultado.append(missao_resp)
        
    return resultado

@app.post("/missoes/{missao_id}/concluir")
def concluir_missao(missao_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Completar missão."""
    # Verificar se missão existe
    missao = db.query(models.Missao).filter(models.Missao.id == missao_id).first()
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    
    # Verificar se já concluiu
    existente = db.query(models.MissaoConcluida).filter_by(missao_id=missao_id, aluno_id=current_user.id).first()
    if existente:
        raise HTTPException(status_code=400, detail="Missão já enviada para validação")
    
    conclusao = models.MissaoConcluida(missao_id=missao_id, aluno_id=current_user.id)
    db.add(conclusao)
    
    # Streak Logic
    today = datetime.utcnow().date()
    last_activity = current_user.last_activity_date.date() if current_user.last_activity_date else None
    
    if last_activity != today:
        if last_activity == today - timedelta(days=1):
            current_user.streak_count += 1
        else:
            current_user.streak_count = 1
        current_user.last_activity_date = datetime.utcnow()
        
        if current_user.streak_count % 5 == 0:
            current_user.xp += 50
            
    db.commit()
    logger.info(f"Mission completed: {missao.titulo} by {current_user.nome}")
    return {"message": "Missão enviada para validação!"}

@app.get("/missoes/submetidas")
def read_missoes_submetidas(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel not in ['professor', 'gestor']:
        raise HTTPException(status_code=403, detail="Apenas professores podem ver submissões")
    
    submissoes = db.query(models.MissaoConcluida).join(models.Missao).filter(
        models.MissaoConcluida.validada == False,
        models.Missao.criador_id == current_user.id
    ).all()
    
    resultado = []
    for sub in submissoes:
        resultado.append({
            "id": sub.id,
            "aluno_nome": sub.aluno.nome,
            "aluno_serie": sub.aluno.serie_nome,
            "missao_titulo": sub.missao.titulo,
            "data_solicitacao": sub.data_solicitacao
        })
    return resultado

@app.post("/missoes/validar/{submissao_id}")
def validar_missao(submissao_id: int, aprovado: bool, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel not in ['professor', 'gestor']:
        raise HTTPException(status_code=403, detail="Apenas professores podem validar missões")
        
    submissao = db.query(models.MissaoConcluida).filter(models.MissaoConcluida.id == submissao_id).first()
    if not submissao:
        raise HTTPException(status_code=404, detail="Submissão não encontrada")
        
    if submissao.validada:
        raise HTTPException(status_code=400, detail="Esta missão já foi validada")
        
    submissao.validada = True
    submissao.validada_por = current_user.id
    submissao.data_validacao = datetime.utcnow()
    
    if aprovado:
        aluno = submissao.aluno
        missao = submissao.missao
        
        aluno.xp += missao.pontos
        aluno.moedas += missao.moedas
        
        novo_nivel = 1 + (aluno.xp // 100)
        if novo_nivel > aluno.nivel:
            aluno.nivel = novo_nivel
            
        logger.info(f"Mission approved: {missao.titulo} for {aluno.nome}")
    else:
        # Se rejeitado, remover a submissão para permitir nova tentativa
        logger.info(f"Mission rejected: {submissao.missao.titulo} for {submissao.aluno.nome}")
        db.delete(submissao)
        db.commit()
        return {"message": "Missão rejeitada e removida para nova tentativa"}

    db.commit()
    return {"message": "Missão validada com sucesso!"}

@app.post("/users/import")
async def import_users(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'gestor':
        raise HTTPException(status_code=403, detail="Apenas gestores podem importar usuários")
    
    content = await file.read()
    # Use utf-8-sig to handle BOM from Excel
    try:
        decoded_content = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            decoded_content = content.decode('latin-1')
        except:
            raise HTTPException(status_code=400, detail="Erro de codificação do arquivo. Use UTF-8.")

    csv_reader = csv.DictReader(io.StringIO(decoded_content))
    
    # Validate headers
    if not csv_reader.fieldnames or 'email' not in csv_reader.fieldnames or 'nome' not in csv_reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV inválido. Colunas obrigatórias: nome, email")

    count = 0
    errors = []
    row_num = 1
    
    for row in csv_reader:
        row_num += 1
        email = row.get('email', '').strip()
        if not email:
            continue
            
        try:
            # Check if user exists
            if db.query(models.User).filter(models.User.email == email).first():
                errors.append(f"Linha {row_num}: Email {email} já cadastrado")
                continue

            # Resolve serie_id if provided
            serie_id = None
            serie_nome = row.get('serie')
            if serie_nome:
                serie = db.query(models.Serie).filter(
                    models.Serie.nome == serie_nome,
                    models.Serie.escola_id == current_user.escola_id
                ).first()
                if serie:
                    serie_id = serie.id
            
            db_user = models.User(
                email=email,
                nome=row.get('nome', '').strip(),
                senha_hash=auth.get_password_hash(row.get('senha', 'senha123')),
                papel=row.get('papel', 'aluno').lower(),
                serie_id=serie_id,
                disciplina=row.get('disciplina'),
                escola_id=current_user.escola_id
            )
            db.add(db_user)
            count += 1
        except Exception as e:
            errors.append(f"Linha {row_num} ({email}): {str(e)}")
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction error during import: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar dados no banco")

    logger.info(f"Users imported: {count} successful, {len(errors)} errors")
    return {"imported": count, "errors": errors}

@app.delete("/users/all")
def delete_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'gestor':
        raise HTTPException(status_code=403, detail="Apenas gestores podem deletar usuários")
    
    deleted = db.query(models.User).filter(models.User.papel == 'aluno', models.User.escola_id == current_user.escola_id).delete()
    db.commit()
    logger.warning(f"All students deleted by {current_user.nome}: {deleted} users")
    return {"deleted": deleted}

@app.put("/users/me/profile", response_model=schemas.UserResponse)
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

@app.post("/users/me/avatar", response_model=schemas.UserResponse)
async def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Validar arquivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
    
    # Verificar tamanho (ler o arquivo para memória para checar tamanho - cuidado com arquivos muito grandes em prod)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024: # 5MB
        raise HTTPException(status_code=400, detail="Imagem deve ter no máximo 5MB")

    # Salvar o arquivo de avatar no disco
    avatar_dir = os.path.join(os.getcwd(), "media", "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    
    # Sanitize filename
    safe_filename = "".join([c for c in file.filename if c.isalnum() or c in ('._-')]).strip()
    if not safe_filename:
        safe_filename = "avatar.png"
        
    # Nome único para evitar colisões
    filename = f"user_{current_user.id}_{int(datetime.utcnow().timestamp())}_{safe_filename}"
    file_path = os.path.join(avatar_dir, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        logger.error(f"Error saving avatar file: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar imagem")
        
    # Atualizar URL do avatar no usuário (caminho relativo para servir via /media)
    # Ensure forward slashes for URL
    current_user.avatar_url = f"/media/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
    logger.info(f"Avatar uploaded and saved for {current_user.email} at {current_user.avatar_url}")
    return current_user

@app.get("/users/me/inventory")
def get_inventory(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    inventario = db.query(models.UserItem).filter(models.UserItem.user_id == current_user.id).all()
    return inventario

@app.post("/loja/comprar/{item_id}")
def comprar_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    
    if current_user.moedas < item.preco_moedas:
        raise HTTPException(status_code=400, detail="Moedas insuficientes")
    
    current_user.moedas -= item.preco_moedas
    
    inventario_item = models.UserItem(user_id=current_user.id, item_id=item_id)
    db.add(inventario_item)
    
    # Registrar transação
    transacao = models.Transacao(
        user_id=current_user.id,
        tipo='compra',
        descricao=f"Comprou {item.nome}",
        moedas=-item.preco_moedas
    )
    db.add(transacao)
    
    db.commit()
    logger.info(f"Item purchased: {item.nome} by {current_user.nome}")
    return {"message": f"Item {item.nome} comprado com sucesso!"}

@app.get("/loja/itens")
def listar_itens(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    itens = db.query(models.Item).all()
    return itens

@app.post("/lootbox/abrir")
def open_lootbox(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    custo_lootbox = 50
    
    if current_user.moedas < custo_lootbox:
        raise HTTPException(status_code=400, detail="Moedas insuficientes para abrir lootbox")
    
    current_user.moedas -= custo_lootbox
    
    raridades = ['comum', 'raro', 'epico', 'lendario']
    pesos = [50, 30, 15, 5]
    raridade = random.choices(raridades, weights=pesos, k=1)[0]
    
    itens_disponiveis = db.query(models.Item).filter(models.Item.raridade == raridade).all()
    
    if not itens_disponiveis:
        itens_disponiveis = db.query(models.Item).filter(models.Item.raridade == 'comum').all()
    
    if not itens_disponiveis:
        raise HTTPException(status_code=500, detail="Nenhum item disponível")
    
    item_ganho = random.choice(itens_disponiveis)
    
    inventario_item = models.UserItem(user_id=current_user.id, item_id=item_ganho.id)
    db.add(inventario_item)
    
    # Registrar transação
    transacao = models.Transacao(
        user_id=current_user.id,
        tipo='lootbox',
        descricao=f"Abriu lootbox e ganhou {item_ganho.nome}",
        moedas=-custo_lootbox
    )
    db.add(transacao)
    
    db.commit()
    logger.info(f"Lootbox opened: {item_ganho.nome} ({raridade}) by {current_user.nome}")
    return {
        "message": "Lootbox aberta!",
        "item": {
            "id": item_ganho.id,
            "nome": item_ganho.nome,
            "raridade": item_ganho.raridade,
            "tipo": item_ganho.tipo
        }
    }

@app.post("/inventario/{inventario_id}/equipar")
def equipar_item(inventario_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    inventario_item = db.query(models.UserItem).filter(
        models.UserItem.id == inventario_id,
        models.UserItem.user_id == current_user.id
    ).first()
    
    if not inventario_item:
        raise HTTPException(status_code=404, detail="Item não encontrado no inventário")
    
    db.query(models.UserItem).filter(
        models.UserItem.user_id == current_user.id,
        models.UserItem.equipado == True
    ).update({"equipado": False})
    
    inventario_item.equipado = True
    db.commit()
    logger.info(f"Item equipped: {inventario_item.item.nome} by {current_user.nome}")
    return {"message": "Item equipado com sucesso!"}

@app.get("/ranking")
def get_ranking(limit: int = 10, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    ranking = db.query(models.User).filter(
        models.User.papel == 'aluno',
        models.User.escola_id == current_user.escola_id
    ).order_by(models.User.xp.desc()).limit(limit).all()
    
    return [
        {
            "nome": user.nome,
            "nivel": user.nivel,
            "xp": user.xp,
            "serie": user.serie_nome
        } for user in ranking
    ]

@app.get("/reports/stats")
def get_reports_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
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
    # (Simplificado, em prod faria via query SQL AVG)
    all_students = db.query(models.User).filter(models.User.papel == 'aluno', models.User.escola_id == current_user.escola_id).all()
    avg_xp = sum([u.xp for u in all_students]) / len(all_students) if all_students else 0
    
    return {
        "total_alunos": total_alunos,
        "total_missoes": total_missoes,
        "media_xp": int(avg_xp),
        "top_alunos": top_alunos_data
    }

# --- Clan System ---

@app.post("/clans/", response_model=schemas.ClanResponse)
def create_clan(clan: schemas.ClanCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    if current_user.papel != 'aluno':
        raise HTTPException(status_code=403, detail="Apenas alunos podem criar clãs")
    
    # Verificar se já está em um clã
    existing_membership = db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first()
    if existing_membership:
        raise HTTPException(status_code=400, detail="Você já está em um clã")
        
    # Verificar nome único
    if db.query(models.Clan).filter(models.Clan.nome == clan.nome).first():
        raise HTTPException(status_code=400, detail="Nome de clã já existe")
        
    db_clan = models.Clan(
        nome=clan.nome,
        descricao=clan.descricao,
        lider_id=current_user.id,
        escola_id=current_user.escola_id
    )
    db.add(db_clan)
    db.commit()
    db.refresh(db_clan)
    
    # Adicionar líder como membro
    member = models.ClanMember(clan_id=db_clan.id, user_id=current_user.id, papel="lider")
    try:
        db.add(member)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating clan member: {e}")
        raise HTTPException(status_code=500, detail="Erro ao adicionar líder ao clã")
    
    logger.info(f"Clan created: {clan.nome} by {current_user.nome}")
    return db_clan

@app.get("/clans/me", response_model=Optional[schemas.ClanResponse])
def get_my_clan(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    membership = db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first()
    if not membership:
        return None
    return membership.clan

@app.get("/clans/{clan_id}/members", response_model=list[schemas.ClanMemberResponse])
def get_clan_members(clan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    members = db.query(models.ClanMember).filter(models.ClanMember.clan_id == clan_id).all()
    return [
        schemas.ClanMemberResponse(
            id=m.id,
            user_id=m.user_id,
            user_nome=m.user.nome,
            papel=m.papel,
            user_avatar=m.user.avatar_url
        ) for m in members
    ]

@app.post("/clans/invite")
def invite_to_clan(email: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Verificar se é líder
    membership = db.query(models.ClanMember).filter(
        models.ClanMember.user_id == current_user.id,
        models.ClanMember.papel == 'lider'
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Apenas o líder pode convidar")
        
    target_user = db.query(models.User).filter(models.User.email == email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    if target_user.escola_id != current_user.escola_id:
        raise HTTPException(status_code=400, detail="Usuário deve ser da mesma escola")
        
    # Verificar se já está em clã
    if db.query(models.ClanMember).filter(models.ClanMember.user_id == target_user.id).first():
        raise HTTPException(status_code=400, detail="Usuário já está em um clã")
        
    # Criar convite
    invite = models.ClanInvite(
        clan_id=membership.clan_id,
        destinatario_email=email
    )
    db.add(invite)
    db.commit()
    return {"message": f"Convite enviado para {email}"}

@app.get("/clans/invites/my", response_model=list[schemas.ClanInviteResponse])
def get_my_invites(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    invites = db.query(models.ClanInvite).filter(
        models.ClanInvite.destinatario_email == current_user.email,
        models.ClanInvite.status == 'pendente'
    ).all()
    
    return [
        schemas.ClanInviteResponse(
            id=inv.id,
            clan_id=inv.clan_id,
            clan_nome=inv.clan.nome,
            status=inv.status,
            criado_em=inv.criado_em
        ) for inv in invites
    ]

@app.post("/clans/invites/{invite_id}/accept")
def accept_invite(invite_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    invite = db.query(models.ClanInvite).filter(models.ClanInvite.id == invite_id).first()
    if not invite or invite.destinatario_email != current_user.email:
        raise HTTPException(status_code=404, detail="Convite não encontrado")
        
    if invite.status != 'pendente':
        raise HTTPException(status_code=400, detail="Convite inválido")
        
    # Verificar novamente se já tem clã
    if db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Você já está em um clã")
        
    # Aceitar
    invite.status = 'aceito'
    member = models.ClanMember(clan_id=invite.clan_id, user_id=current_user.id)
    db.add(member)
    db.commit()
    return {"message": f"Bem-vindo ao clã {invite.clan.nome}!"}

@app.post("/clans/leave")
def leave_clan(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    membership = db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first()
    if not membership:
        raise HTTPException(status_code=400, detail="Você não está em um clã")
        
    if membership.papel == 'lider':
        # Se for líder, deletar clã (simplificação) ou passar liderança
        # Por enquanto, deleta o clã se for o único, ou impede se tiver membros
        members_count = db.query(models.ClanMember).filter(models.ClanMember.clan_id == membership.clan_id).count()
        if members_count > 1:
            raise HTTPException(status_code=400, detail="Líder não pode sair sem passar a liderança ou remover todos os membros")
        else:
            # Deletar clã
            db.delete(membership.clan)
    else:
        db.delete(membership)
    db.commit()
    return {"message": "Você saiu do clã"}

@app.get("/clans/suggestions", response_model=list[schemas.ClanResponse])
def get_clan_suggestions(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Retorna sugestões de clãs (por enquanto, todos os clãs da escola do aluno)."""
    if not current_user.escola_id:
        return []
        
    clans = db.query(models.Clan).filter(models.Clan.escola_id == current_user.escola_id).limit(5).all()
    return clans
        


# --- Mural System ---

@app.get("/mural", response_model=list[schemas.MuralPostResponse])
def get_mural_posts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    posts = db.query(models.MuralPost).order_by(models.MuralPost.criado_em.desc()).offset(skip).limit(limit).all()
    
    results = []
    for post in posts:
        results.append(schemas.MuralPostResponse(
            id=post.id,
            user_id=post.user_id,
            user_nome=post.user.nome,
            user_avatar=post.user.avatar_url,
            conteudo=post.conteudo,
            imagem_url=post.imagem_url,
            likes=post.likes,
            criado_em=post.criado_em,
            liked_by_me=False 
        ))
    return results

@app.post("/mural", response_model=schemas.MuralPostResponse)
def create_mural_post(post: schemas.MuralPostCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_post = models.MuralPost(
        user_id=current_user.id,
        conteudo=post.conteudo,
        imagem_url=post.imagem_url
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return schemas.MuralPostResponse(
        id=db_post.id,
        user_id=db_post.user_id,
        user_nome=current_user.nome,
        user_avatar=current_user.avatar_url,
        conteudo=db_post.conteudo,
        imagem_url=db_post.imagem_url,
        likes=db_post.likes,
        criado_em=db_post.criado_em,
        liked_by_me=False
    )

@app.post("/mural/{post_id}/like")
def like_mural_post(post_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    post = db.query(models.MuralPost).filter(models.MuralPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    post.likes += 1
    db.commit()
    
    return {"message": "Post curtido", "likes": post.likes}

@app.delete("/mural/{post_id}")
def delete_mural_post(post_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    post = db.query(models.MuralPost).filter(models.MuralPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    
    if current_user.papel != 'admin' and current_user.papel != 'gestor' and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    db.delete(post)
    db.commit()
    return {"message": "Post excluído"}

@app.delete("/clans/{clan_id}")
def delete_clan(clan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    clan = db.query(models.Clan).filter(models.Clan.id == clan_id).first()
    if not clan:
        raise HTTPException(status_code=404, detail="Clã não encontrado")
        
    if current_user.papel != 'admin' and current_user.papel != 'gestor' and clan.lider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    db.delete(clan)
    db.commit()
    return {"message": "Clã excluído"}

# --- New Features (Phase 4) ---

@app.get("/users/search", response_model=list[schemas.UserResponse])
def search_users(q: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Buscar alunos da mesma escola que não estão em clã."""
    if not q:
        return []
        
    # Buscar alunos da mesma escola, que contenham 'q' no nome ou email
    # Buscar alunos da mesma escola, que contenham 'q' no nome ou email
    # Using python-side filtering for case-insensitivity compatibility if needed, 
    # but try ILIKE or lower() first. SQLite doesn't support ILIKE by default.
    # We will use lower() for compatibility.
    users = db.query(models.User).filter(
        models.User.escola_id == current_user.escola_id,
        models.User.papel == 'aluno'
    ).all()
    
    # Filter in python to be safe with SQLite/Postgres differences for now
    q_lower = q.lower()
    users = [u for u in users if q_lower in u.nome.lower() or q_lower in u.email.lower()]
    
    # Filtrar os que já têm clã (idealmente faria no SQL com NOT EXISTS, mas aqui simplificado)
    available_users = []
    for user in users:
        in_clan = db.query(models.ClanMember).filter(models.ClanMember.user_id == user.id).first()
        if not in_clan:
            available_users.append(user)
            
    return available_users

@app.get("/clans/suggestions", response_model=list[schemas.ClanResponse])
def suggest_clans(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Sugere clãs da mesma escola (aleatórios ou top)."""
    clans = db.query(models.Clan).filter(
        models.Clan.escola_id == current_user.escola_id
    ).limit(5).all()
    return clans

@app.get("/users/me/qrcode")
def get_my_qrcode(current_user: models.User = Depends(auth.get_current_user)):
    """Gera QR Code para o usuário."""
    # Dados do QR Code (pode ser um token de validação ou ID)
    data = f"schoolquest:user:{current_user.id}:{current_user.email}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Converter para base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return {"qrcode_base64": f"data:image/png;base64,{img_str}"}

class QRCodeRequest(BaseModel):
    qr_data: str

@app.post("/users/validate_qrcode")
def validate_qrcode(request: QRCodeRequest, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Valida QR Code e retorna dados do aluno."""
    if current_user.papel not in ['professor', 'gestor']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Format: schoolquest:user:{id}:{email}
    try:
        parts = request.qr_data.split(":")
        if len(parts) != 4 or parts[0] != "schoolquest" or parts[1] != "user":
            raise HTTPException(status_code=400, detail="QR Code inválido")
            
        user_id = int(parts[2])
        user_email = parts[3]
        
        user = db.query(models.User).filter(models.User.id == user_id, models.User.email == user_email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")
            
        return {
            "nome": user.nome,
            "serie": user.serie_nome,
            "nivel": user.nivel,
            "xp": user.xp,
            "avatar_url": user.avatar_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Erro ao processar QR Code")

@app.get("/reports/top_professors")
def get_top_professors(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Retorna professores com mais missões concluídas pelos alunos."""
    if current_user.papel not in ['gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    # Esta query é complexa, vamos simplificar: contar missões concluídas agrupadas por criador da missão
    # SQL: SELECT criador_id, COUNT(*) FROM missoes JOIN missoes_concluidas ... GROUP BY criador_id
    
    # Abordagem Python (menos eficiente mas funciona para MVP)
    professores = db.query(models.User).filter(
        models.User.papel == 'professor', 
        models.User.escola_id == current_user.escola_id
    ).all()
    
    result = []
    for prof in professores:
        # Contar missões deste professor que foram concluídas e validadas
        count = db.query(models.MissaoConcluida).join(models.Missao).filter(
            models.Missao.criador_id == prof.id,
            models.MissaoConcluida.validada == True
        ).count()
        result.append({"nome": prof.nome, "missoes_concluidas": count})
        
    # Ordenar
    result.sort(key=lambda x: x['missoes_concluidas'], reverse=True)
    return result[:5]

@app.get("/reports/participation")
def get_participation_stats(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Retorna participação por série (XP total)."""
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

@app.get("/reports/top_schools")
def get_top_schools(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Retorna escolas com mais XP total (Admin only)."""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    escolas = db.query(models.Escola).all()
    result = []
    for escola in escolas:
        # Somar XP de todos os alunos da escola
        total_xp = 0
        alunos = db.query(models.User).filter(models.User.escola_id == escola.id, models.User.papel == 'aluno').all()
        for aluno in alunos:
            total_xp += aluno.xp
        result.append({"nome": escola.nome, "total_xp": total_xp})
        
    result.sort(key=lambda x: x['total_xp'], reverse=True)
    return result[:10]
