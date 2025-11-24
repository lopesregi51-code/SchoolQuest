"""
Sistema de backup automático do banco de dados SQLite.
Cria backups periódicos para evitar perda de dados durante desenvolvimento.
"""
import shutil
import os
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseBackup:
    def __init__(self, db_path: str = "schoolquest.db", backup_dir: str = "backups"):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, prefix: str = "auto") -> str:
        """Cria um backup do banco de dados."""
        if not self.db_path.exists():
            logger.warning(f"Database file {self.db_path} does not exist, skipping backup")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{prefix}_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"✓ Backup created: {backup_path}")
            
            # Manter apenas os últimos 10 backups automáticos
            self._cleanup_old_backups(prefix, keep=10)
            
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def _cleanup_old_backups(self, prefix: str, keep: int = 10):
        """Remove backups antigos, mantendo apenas os mais recentes."""
        backups = sorted(
            [f for f in self.backup_dir.glob(f"{prefix}_backup_*.db")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for old_backup in backups[keep:]:
            try:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup.name}")
            except Exception as e:
                logger.error(f"Failed to remove old backup {old_backup}: {e}")
    
    def restore_latest(self, prefix: str = "auto") -> bool:
        """Restaura o backup mais recente."""
        backups = sorted(
            [f for f in self.backup_dir.glob(f"{prefix}_backup_*.db")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not backups:
            logger.warning(f"No backups found with prefix '{prefix}'")
            return False
        
        latest_backup = backups[0]
        try:
            shutil.copy2(latest_backup, self.db_path)
            logger.info(f"✓ Database restored from: {latest_backup}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> list:
        """Lista todos os backups disponíveis."""
        backups = sorted(
            self.backup_dir.glob("*_backup_*.db"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        return [
            {
                "name": b.name,
                "size": b.stat().st_size,
                "modified": datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
            for b in backups
        ]

# Instância global
backup_manager = DatabaseBackup()
