from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging
from datetime import datetime, timedelta
from . import models, schemas, database, auth
from .routers import shop, mural, chat, mobile, analytics
from .websocket import manager, NotificationType
from .config import settings
import os
from io import BytesIO
from fastapi.staticfiles import StaticFiles
from PIL import Image

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
app.include_router(chat.router)
app.include_router(mobile.router)
app.include_router(analytics.router)

# Static files
app.mount("/media", StaticFiles(directory="media"), name="media")
# Mount uploads directory for avatars
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Create default users on startup and backup database."""
    # Importar backup manager
    from .db_backup import backup_manager
    
    # Criar backup antes de qualquer operação
    logger.info("Creating automatic backup on startup...")
    backup_manager.create_backup(prefix="startup")
    
    db = database.SessionLocal()
    try:
        # Check for admin user
        admin = db.query(models.User).filter(models.User.email == "admin@test.com").first()
        if not admin:
            logger.info("Creating default admin user...")
            
            # Create admin school first
            admin_school = db.query(models.Escola).filter(models.Escola.nome == "Escola Administração").first()
            if not admin_school:
                admin_school = models.Escola(nome="Escola Administração")
                db.add(admin_school)
                db.flush()
                logger.info(f"Admin school created: {admin_school.nome}")
            
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
            logger.info("Default admin user created: admin@test.com / admin123")
        else:
            logger.info("Admin user already exists.")
            # Ensure admin has escola_id
            if not admin.escola_id:
                admin_school = db.query(models.Escola).filter(models.Escola.nome == "Escola Administração").first()
                if not admin_school:
                    admin_school = models.Escola(nome="Escola Administração")
                    db.add(admin_school)
                    db.flush()
                admin.escola_id = admin_school.id
                db.commit()
                logger.info(f"Admin escola_id updated to {admin.escola_id}")
    except Exception as e:
        logger.error(f"Error creating default users: {e}")
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    """Backup database on shutdown."""
    from .db_backup import backup_manager
    logger.info("Creating automatic backup on shutdown...")
    backup_manager.create_backup(prefix="shutdown")


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

# Public endpoint to reinitialize database (useful after deployment issues)
@app.post("/init-db")
def init_database(db: Session = Depends(get_db)):
    """Public endpoint to initialize database with default admin user (emergency recovery)."""
    try:
        # Check for admin user
        admin = db.query(models.User).filter(models.User.email == "admin@test.com").first()
        
        if admin:
            # Admin exists, ensure it has escola_id
            if not admin.escola_id:
                admin_school = db.query(models.Escola).filter(models.Escola.nome == "Escola Administração").first()
                if not admin_school:
                    admin_school = models.Escola(nome="Escola Administração")
                    db.add(admin_school)
                    db.flush()
                admin.escola_id = admin_school.id
                db.commit()
                return {"message": "Admin user updated", "email": "admin@test.com", "password": "admin123"}
            return {"message": "Admin user already exists", "email": "admin@test.com", "password": "admin123"}
        
        # Create admin school
        admin_school = db.query(models.Escola).filter(models.Escola.nome == "Escola Administração").first()
        if not admin_school:
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
        
        return {
            "message": "Admin user created successfully",
            "email": "admin@test.com",
            "password": "admin123"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error in init-db: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize database: {str(e)}")


# WebSocket endpoint for real-time notifications
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(f"pong: {data}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        manager.disconnect(user_id)

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

@app.get("/admin/backups")
def list_backups(current_user: models.User = Depends(auth.get_current_user)):
    """Lista todos os backups disponíveis (apenas admin)."""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem acessar backups")
    
    from .db_backup import backup_manager
    backups = backup_manager.list_backups()
    return {"backups": backups, "total": len(backups)}

@app.post("/admin/backup/create")
def create_manual_backup(current_user: models.User = Depends(auth.get_current_user)):
    """Cria um backup manual do banco de dados (apenas admin)."""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar backups")
    
    from .db_backup import backup_manager
    backup_path = backup_manager.create_backup(prefix="manual")
    
    if backup_path:
        return {"message": "Backup criado com sucesso", "path": backup_path}
    else:
        raise HTTPException(status_code=500, detail="Erro ao criar backup")

@app.post("/admin/backup/restore/{backup_name}")
def restore_backup(backup_name: str, current_user: models.User = Depends(auth.get_current_user)):
    """Restaura um backup específico (apenas admin)."""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem restaurar backups")
    
    from .db_backup import backup_manager
    # Extract prefix from backup name
    prefix = backup_name.split("_backup_")[0] if "_backup_" in backup_name else "manual"
    
    success = backup_manager.restore_latest(prefix=prefix)
    
    if success:
        return {"message": f"Backup {backup_name} restaurado com sucesso"}
    else:
        raise HTTPException(status_code=500, detail="Erro ao restaurar backup")

@app.post("/admin/clear-all")
def clear_all_data(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Apaga todos os registros de todas as tabelas (mantém a estrutura)."""
    if current_user.papel != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem limpar dados")
    try:
        # Delete in order respecting foreign key constraints
        # First: tables that reference other tables (children)
        # Last: tables that are referenced (parents)
        
        tables_order = [
            # Level 1: Tables that reference User, Missao, Clan, etc
            models.PostLike,
            models.ClanMessage,
            models.DeviceToken,
            models.UserConquista,
            models.Purchase,
            models.MissaoAtribuida,
            models.MissaoConcluida,
            models.UserItem,
            models.Transacao,
            models.ClanMember,
            models.ClanInvite,
            
            # Level 2: Tables that reference basic entities
            models.MuralPost,
            models.Clan,
            models.Missao,
            
            # Level 3: Independent or simple FK tables
            models.Reward,
            models.Conquista,
            models.Item,
            
            # Level 4: User references Serie and Escola
            models.User,
            
            # Level 5: Serie references Escola
            models.Serie,
            
            # Level 6: Final parent table
            models.Escola,
        ]
        
        for tbl in tables_order:
            db.query(tbl).delete()
        
        db.commit()
        logger.info(f"Admin {current_user.email} limpou todas as tabelas")
        return {"message": "Todos os dados foram apagados (estrutura mantida)"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing data: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao limpar dados: {str(e)}")

from fastapi import Form
from fastapi.responses import Response
import pandas as pd
from . import csv_handler

@app.post("/admin/upload-csv")
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
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem fazer upload de CSV")
    
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
        df = pd.read_csv(io.BytesIO(contents))
        
        logger.info(f"Processing CSV upload: type={tipo}, rows={len(df)}, user={current_user.email}")
        
        # Process based on type
        if tipo == "escolas":
            result = csv_handler.process_escolas_csv(df, db)
        elif tipo == "gestores":
            result = csv_handler.process_gestores_csv(df, db)
        elif tipo == "usuarios":
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

@app.get("/admin/csv-template/{tipo}")
def download_csv_template(
    tipo: str,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Download template CSV para upload"""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem baixar templates")
    
    templates = {
        "escolas": "nome\nEscola Exemplo\n",
        "gestores": "nome,email,senha,escola_nome\nCarlos Silva,carlos@escola.com,senha123,Escola Exemplo\n",
        "usuarios": "nome,email,senha,papel,serie,disciplina,escola_nome\nJoão Aluno,joao@aluno.com,senha123,aluno,5º Ano,,Escola Exemplo\nProf. Ana,ana@prof.com,profsenha,professor,,,Matemática,Escola Exemplo\n"
    }
    
    if tipo not in templates:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    
    return Response(
        content=templates[tipo],
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={tipo}_template.csv"}
    )

# ==================== END CSV ENDPOINTS ====================


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

    import uuid
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
    db.delete(escola)
    db.commit()
    return {"message": "Escola excluída com sucesso"}

@app.get("/clans/", response_model=list[schemas.ClanResponse])
def read_clans(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar clãs da escola do usuário."""
    if not current_user.escola_id:
        return []
        
    return db.query(models.Clan).filter(models.Clan.escola_id == current_user.escola_id).all()

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
        "escola_nome": current_user.escola.nome if current_user.escola else None,
        "qr_token": current_user.qr_token
    }
    return user_dict

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


@app.post("/users/{user_id}/avatar", response_model=schemas.UserResponse)
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
    mural_posts = db.query(models.MuralPost).filter(models.MuralPost.user_id == user.id).order_by(models.MuralPost.data_criacao.desc()).limit(5).all()
    
    profile_data["posts"] = [
        {
            "id": post.id,
            "conteudo": post.texto,  # Fixed: MuralPost uses 'texto' not 'conteudo'
            "likes": len(post.likes) if post.likes else 0,  # Fixed: count likes
            "data": post.data_criacao
        } for post in mural_posts
    ]
    
    return profile_data

@app.put("/users/{user_id}", response_model=schemas.UserResponse)
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


@app.get("/missoes/", response_model=list[schemas.MissaoResponse])
def read_missoes(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar todas as missões disponíveis."""
    try:
        if current_user.papel == 'aluno':
            logger.info(f"Fetching missions for student: {current_user.nome} (escola_id: {current_user.escola_id})")
            
            # Students see missions from their school - using JOIN instead of subquery
            missoes = db.query(models.Missao).join(
                models.User, models.Missao.criador_id == models.User.id
            ).filter(
                models.User.escola_id == current_user.escola_id
            ).all()
            
            logger.info(f"Found {len(missoes)} school missions for student {current_user.nome}")
            
            # Add clan missions if student is in a clan
            clan_member = db.query(models.ClanMember).filter(models.ClanMember.user_id == current_user.id).first()
            if clan_member:
                clan_missions = db.query(models.Missao).filter(
                    models.Missao.tipo == 'clan',
                    models.Missao.clan_id == clan_member.clan_id
                ).all()
                logger.info(f"Found {len(clan_missions)} clan missions for student {current_user.nome}")
                missoes.extend(clan_missions)
            
            # Add status for each mission
            result = []
            for missao in missoes:
                missao_dict = {
                    "id": missao.id,
                    "titulo": missao.titulo,
                    "descricao": missao.descricao,
                    "pontos": missao.pontos,
                    "moedas": missao.moedas,
                    "categoria": missao.categoria,
                    "criador_id": missao.criador_id,
                    "tipo": missao.tipo,
                    "clan_id": missao.clan_id,
                    "criado_em": missao.criado_em,
                    "status": "disponivel"  # default
                }
                
                # Check if student has completed this mission
                conclusao = db.query(models.MissaoConcluida).filter(
                    models.MissaoConcluida.missao_id == missao.id,
                    models.MissaoConcluida.aluno_id == current_user.id
                ).first()
                
                if conclusao:
                    if conclusao.validada:
                        missao_dict["status"] = "aprovada"
                    else:
                        missao_dict["status"] = "pendente"
                
                result.append(missao_dict)
            
            logger.info(f"Returning {len(result)} missions for student {current_user.nome}")
            return result
        else:
            # Professors and managers see all missions from their school - using JOIN
            logger.info(f"Fetching missions for {current_user.papel}: {current_user.nome} (escola_id: {current_user.escola_id})")
            
            missoes = db.query(models.Missao).join(
                models.User, models.Missao.criador_id == models.User.id
            ).filter(
                models.User.escola_id == current_user.escola_id
            ).all()
            
            logger.info(f"Returning {len(missoes)} missions for {current_user.papel} {current_user.nome}")
            return missoes
    except Exception as e:
        logger.error(f"Error fetching missions for user {current_user.nome}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar missões: {str(e)}")

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
    logger.info(f"Mission deleted: {missao.titulo} by {current_user.nome}")
    return {"message": "Missão excluída com sucesso!"}

@app.post("/missoes/{missao_id}/completar")
def completar_missao(missao_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Aluno marca missão como concluída (pendente de validação)."""
    if current_user.papel != 'aluno':
        raise HTTPException(status_code=403, detail="Apenas alunos podem completar missões")
    
    missao = db.query(models.Missao).filter(models.Missao.id == missao_id).first()
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
    
    # Check if already completed
    existing = db.query(models.MissaoConcluida).filter(
        models.MissaoConcluida.missao_id == missao_id,
        models.MissaoConcluida.aluno_id == current_user.id
    ).first()
    
    if existing:
        if existing.validada:
            raise HTTPException(status_code=400, detail="Você já completou esta missão")
        else:
            raise HTTPException(status_code=400, detail="Esta missão já está pendente de validação")
    
    # Create completion record
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

@app.get("/missoes/pendentes")
def read_missoes_pendentes(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar missões pendentes de validação (para professor)."""
    if current_user.papel not in ['professor', 'gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas professores podem ver missões pendentes")
    
    try:
        logger.info(f"Fetching pending missions for {current_user.papel}: {current_user.nome}")
        
        # Get pending missions for missions created by this professor
        pendentes = db.query(models.MissaoConcluida).join(models.Missao).filter(
            models.MissaoConcluida.validada == False,
            models.Missao.criador_id == current_user.id
        ).all()
        
        logger.info(f"Found {len(pendentes)} pending missions for {current_user.nome}")
        
        resultado = []
        for pendente in pendentes:
            resultado.append({
                "id": pendente.id,
                "missao_id": pendente.missao_id,
                "missao_titulo": pendente.missao.titulo,
                "aluno_id": pendente.aluno_id,
                "aluno_nome": pendente.aluno.nome,
                "aluno_serie": pendente.aluno.serie_nome if pendente.aluno.serie else "Sem série",
                "data_solicitacao": pendente.data_solicitacao
            })
        
        return resultado
    except Exception as e:
        logger.error(f"Error fetching pending missions for {current_user.nome}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar missões pendentes: {str(e)}")


@app.get("/missoes/recebidas", response_model=list[schemas.MissaoAtribuidaResponse])
def read_missoes_recebidas(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar missões atribuídas ao aluno."""
    if current_user.papel != 'aluno':
        raise HTTPException(status_code=403, detail="Apenas alunos podem acessar esta rota")
    
    missoes_atribuidas = db.query(models.MissaoAtribuida).filter(
        models.MissaoAtribuida.aluno_id == current_user.id,
        models.MissaoAtribuida.status == 'pendente'
    ).all()
    
    return missoes_atribuidas

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
        logger.info(f"Mission rejected: {missao.titulo} for {aluno.nome}")
        
    db.commit()
    return {"message": "Missão validada com sucesso!"}

@app.get("/missoes/professor/concluidas")
def read_professor_completed_missions(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar missões concluídas e validadas criadas pelo professor."""
    if current_user.papel not in ['professor', 'gestor', 'admin']:
        raise HTTPException(status_code=403, detail="Apenas professores podem acessar esta rota")
    
    try:
        logger.info(f"Fetching completed missions for {current_user.papel}: {current_user.nome}")
        
        # Get completed missions for missions created by this professor
        completed = db.query(models.MissaoConcluida).join(models.Missao).filter(
            models.Missao.criador_id == current_user.id,
            models.MissaoConcluida.validada == True
        ).all()
        
        logger.info(f"Found {len(completed)} completed missions for {current_user.nome}")
        
        resultado = []
        for conclusao in completed:
            resultado.append({
                "id": conclusao.id,
                "missao_id": conclusao.missao_id,
                "missao_titulo": conclusao.missao.titulo,
                "aluno_id": conclusao.aluno_id,
                "aluno_nome": conclusao.aluno.nome,
                "aluno_serie": conclusao.aluno.serie_nome if conclusao.aluno.serie else "Sem série",
                "data_validacao": conclusao.data_validacao,
                "validada": conclusao.validada
            })
        
        return resultado
    except Exception as e:
        logger.error(f"Error fetching completed missions for {current_user.nome}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar missões concluídas: {str(e)}")



class ValidacaoPresencialRequest(BaseModel):
    aluno_id: Optional[int] = None
    qr_token: Optional[str] = None

@app.post("/missoes/{missao_id}/validar_presencial")
def validar_missao_presencial(
    missao_id: int,
    request: ValidacaoPresencialRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Valida uma missão presencialmente para um aluno específico (via QR Code ou ID)."""
    # Verificar permissões (professor criador ou admin/gestor)
    missao = db.query(models.Missao).filter(models.Missao.id == missao_id).first()
    if not missao:
        raise HTTPException(status_code=404, detail="Missão não encontrada")
        
    if current_user.papel == 'professor' and missao.criador_id != current_user.id:
        raise HTTPException(status_code=403, detail="Você só pode validar suas próprias missões")
        
    if current_user.papel == 'aluno':
        raise HTTPException(status_code=403, detail="Alunos não podem validar missões")

    # Buscar aluno
    aluno = None
    if request.qr_token:
        aluno = db.query(models.User).filter(models.User.qr_token == request.qr_token).first()
    elif request.aluno_id:
        aluno = db.query(models.User).filter(models.User.id == request.aluno_id).first()
        
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    # Verificar se já completou
    conclusao = db.query(models.MissaoConcluida).filter(
        models.MissaoConcluida.missao_id == missao_id,
        models.MissaoConcluida.aluno_id == aluno.id
    ).first()
    
    if conclusao:
        if conclusao.validada:
            return {"message": "Missão já foi validada para este aluno", "status": "already_validated", "aluno": aluno.nome}
        else:
            # Já enviou mas não validou -> Validar agora
            conclusao.validada = True
            conclusao.data_validacao = datetime.utcnow()
            conclusao.validada_por = current_user.id
            
            # Dar recompensas
            if missao.tipo == 'clan':
                clan_member = db.query(models.ClanMember).filter(models.ClanMember.user_id == aluno.id).first()
                if clan_member:
                    clan_member.clan.moedas += missao.moedas
            else:
                aluno.xp += missao.pontos
                aluno.moedas += missao.moedas
                if aluno.xp >= aluno.nivel * 1000:
                    aluno.nivel += 1
            
            db.commit()
            return {"message": "Missão validada com sucesso!", "status": "validated", "aluno": aluno.nome}
            
    # Criar nova conclusão validada
    nova_conclusao = models.MissaoConcluida(
        missao_id=missao_id,
        aluno_id=aluno.id,
        data_solicitacao=datetime.utcnow(),
        validada=True,
        validada_por=current_user.id,
        data_validacao=datetime.utcnow()
    )
    db.add(nova_conclusao)
    
    # Dar recompensas
    if missao.tipo == 'clan':
        clan_member = db.query(models.ClanMember).filter(models.ClanMember.user_id == aluno.id).first()
        if clan_member:
            clan_member.clan.moedas += missao.moedas
        else:
             # Se for missão de clã mas aluno não tem clã, talvez dar erro ou ignorar?
             # Por enquanto ignoramos a recompensa do clã
             pass
    else:
        aluno.xp += missao.pontos
        aluno.moedas += missao.moedas
        if aluno.xp >= aluno.nivel * 1000:
            aluno.nivel += 1
    
    db.commit()
    
    return {"message": f"Missão validada para {aluno.nome}!", "status": "created_and_validated", "aluno": aluno.nome}

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
    series_created = []  # Track created series
    series_cache = {}  # Cache to avoid repeated queries
    
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
            
            # Create user logic would be here - for now just count
            count += 1
            
        except Exception as e:
            errors.append(f"Linha {row_num}: {str(e)}")
            continue
    
    result = {
        "imported": count,
        "errors": len(errors),
        "error_details": errors
    }
    
    # Add info about created series if any
    if series_created:
        result["series_created"] = list(set(series_created))  # Remove duplicates
        result["message"] = f"{count} usuários importados. {len(result['series_created'])} séries criadas automaticamente: {', '.join(result['series_created'])}"
    
    return result



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

@app.get("/clans/", response_model=list[schemas.ClanResponse])
def read_clans(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """Listar clãs da escola do usuário."""
    if not current_user.escola_id:
        return []
    clans = db.query(models.Clan).filter(models.Clan.escola_id == current_user.escola_id).all()
    return clans

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

@app.get("/clans/{clan_id}/missoes", response_model=list[schemas.MissaoResponse])
def get_clan_missions(clan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Verificar se usuário é membro do clã
    membership = db.query(models.ClanMember).filter(
        models.ClanMember.clan_id == clan_id,
        models.ClanMember.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Você não é membro deste clã")

    missoes = db.query(models.Missao).filter(
        models.Missao.tipo == 'clan',
        models.Missao.clan_id == clan_id
    ).all()
    
    return missoes

@app.get("/clans/{clan_id}/missoes/progress", response_model=list[schemas.ClanMissionProgressResponse])
def get_clan_missions_progress(clan_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Verificar se usuário é líder do clã
    membership = db.query(models.ClanMember).filter(
        models.ClanMember.clan_id == clan_id,
        models.ClanMember.user_id == current_user.id
    ).first()
    
    if not membership or membership.papel != 'lider':
        raise HTTPException(status_code=403, detail="Apenas o líder pode ver o progresso das missões")

    # Buscar missões do clã
    missoes = db.query(models.Missao).filter(
        models.Missao.tipo == 'clan',
        models.Missao.clan_id == clan_id
    ).all()
    
    # Buscar membros do clã
    members = db.query(models.ClanMember).filter(models.ClanMember.clan_id == clan_id).all()
    
    result = []
    for missao in missoes:
        completed = []
        pending = []
        
        # Buscar conclusões validadas para esta missão
        conclusoes = db.query(models.MissaoConcluida).filter(
            models.MissaoConcluida.missao_id == missao.id,
            models.MissaoConcluida.validada == True
        ).all()
        completed_ids = [c.aluno_id for c in conclusoes]
        
        for member in members:
            member_response = schemas.ClanMemberResponse(
                id=member.id,
                user_id=member.user_id,
                user_nome=member.user.nome,
                papel=member.papel,
                user_avatar=member.user.avatar_url
            )
            if member.user_id in completed_ids:
                completed.append(member_response)
            else:
                pending.append(member_response)
                
        result.append({
            "mission": missao,
            "completed_by": completed,
            "pending_by": pending
        })
        
    return result

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
