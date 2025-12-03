from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from datetime import timedelta
import os

from . import models, schemas, database, auth
from .routers import shop, mural, chat, mobile, analytics, missions, admin, system, clans
from .websocket import manager
from .config import settings

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
    expose_headers=["*"],
)

# Criar tabelas
models.Base.metadata.create_all(bind=database.engine)

# Run reverse migration to remove 'ativa' column if it exists
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from remove_ativa_column import remove_ativa_column
    remove_ativa_column()
    logger.info("Reverse migration completed successfully")
except Exception as e:
    logger.warning(f"Reverse migration warning: {e}")


# Routers
app.include_router(shop.router)
app.include_router(mural.router)
app.include_router(chat.router)
app.include_router(mobile.router)
app.include_router(analytics.router)
app.include_router(missions.router)
app.include_router(admin.router)
app.include_router(system.router)
app.include_router(clans.router)

# Serve uploaded files with FileResponse to prevent CORB
@app.get("/media/{file_path:path}")
async def get_media_file(file_path: str):
    """Serve media files with correct Content-Type to prevent CORB."""
    full_path = os.path.join("media", file_path)
    
    # Security check to prevent directory traversal
    if ".." in file_path or not os.path.abspath(full_path).startswith(os.path.abspath("media")):
        svg_content = """
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f8d7da"/>
            <text x="50%" y="50%" font-family="Arial" font-size="16" fill="#721c24" text-anchor="middle" dy=".3em">Acesso Negado</text>
        </svg>
        """
        return Response(content=svg_content, media_type="image/svg+xml")

    if not os.path.exists(full_path):
        svg_content = """
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#e2e3e5"/>
            <text x="50%" y="50%" font-family="Arial" font-size="16" fill="#383d41" text-anchor="middle" dy=".3em">Imagem não encontrada</text>
            <text x="50%" y="65%" font-family="Arial" font-size="12" fill="#383d41" text-anchor="middle" dy=".3em">(Provavelmente deletada)</text>
        </svg>
        """
        return Response(content=svg_content, media_type="image/svg+xml")
    
    # Return FileResponse with explicit CORS headers
    response = FileResponse(full_path)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

# Serve uploaded files with FileResponse to prevent CORB
@app.get("/uploads/{file_path:path}")
async def get_uploaded_file(file_path: str):
    """Serve uploaded files with correct Content-Type to prevent CORB."""
    full_path = os.path.join("uploads", file_path)
    
    # Security check to prevent directory traversal
    if ".." in file_path or not os.path.abspath(full_path).startswith(os.path.abspath("uploads")):
        svg_content = """
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f8d7da"/>
            <text x="50%" y="50%" font-family="Arial" font-size="16" fill="#721c24" text-anchor="middle" dy=".3em">Acesso Negado</text>
        </svg>
        """
        return Response(content=svg_content, media_type="image/svg+xml")

    if not os.path.exists(full_path):
        svg_content = """
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#e2e3e5"/>
            <text x="50%" y="50%" font-family="Arial" font-size="16" fill="#383d41" text-anchor="middle" dy=".3em">Imagem não encontrada</text>
            <text x="50%" y="65%" font-family="Arial" font-size="12" fill="#383d41" text-anchor="middle" dy=".3em">(Provavelmente deletada)</text>
        </svg>
        """
        return Response(content=svg_content, media_type="image/svg+xml")
    
    # Return FileResponse with explicit CORS headers
    response = FileResponse(full_path)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time notifications."""
    try:
        logger.info(f"WebSocket connection attempt for user {user_id}")
        await manager.connect(websocket, user_id)
        logger.info(f"WebSocket connected successfully for user {user_id}")
        while True:
            # Keep the connection alive and listen for messages
            # For now we just keep it open for server-to-client notifications
            data = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id}: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
        manager.disconnect(websocket, user_id)

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
