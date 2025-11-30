from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from .. import models, auth
from ..db_backup import backup_manager

router = APIRouter(
    tags=["system"]
)

logger = logging.getLogger(__name__)

@router.post("/init-db")
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

@router.get("/admin/backups")
def list_backups(current_user: models.User = Depends(auth.get_current_user)):
    """Lista todos os backups disponíveis (apenas admin)."""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem acessar backups")
    
    backups = backup_manager.list_backups()
    return {"backups": backups, "total": len(backups)}

@router.post("/admin/backup/create")
def create_manual_backup(current_user: models.User = Depends(auth.get_current_user)):
    """Cria um backup manual do banco de dados (apenas admin)."""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem criar backups")
    
    backup_path = backup_manager.create_backup(prefix="manual")
    
    if backup_path:
        return {"message": "Backup criado com sucesso", "path": backup_path}
    else:
        raise HTTPException(status_code=500, detail="Erro ao criar backup")

@router.post("/admin/backup/restore/{backup_name}")
def restore_backup(backup_name: str, current_user: models.User = Depends(auth.get_current_user)):
    """Restaura um backup específico (apenas admin)."""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem restaurar backups")
    
    # Extract prefix from backup name
    prefix = backup_name.split("_backup_")[0] if "_backup_" in backup_name else "manual"
    
    success = backup_manager.restore_latest(prefix=prefix)
    
    if success:
        return {"message": f"Backup {backup_name} restaurado com sucesso"}
    else:
        raise HTTPException(status_code=500, detail="Erro ao restaurar backup")

@router.post("/admin/clear-all")
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
