from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    """
    Configuração centralizada da aplicação usando Pydantic Settings.
    Carrega valores de variáveis de ambiente ou usa valores padrão.
    """
    
    # Security
    secret_key: str = "dev-secret-key-CHANGE-IN-PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days
    
    # Database
    database_url: str = "sqlite:///./schoolquest.db"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    
    # Environment
    environment: str = "development"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Converte string de origens CORS em lista."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def validate_secret_key(self) -> None:
        """Valida se a SECRET_KEY é segura o suficiente."""
        if self.environment == "production":
            if len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY deve ter pelo menos 32 caracteres em produção!")
            if "dev" in self.secret_key.lower() or "change" in self.secret_key.lower():
                raise ValueError("SECRET_KEY padrão detectada! Altere para produção!")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
_settings = None

def get_settings() -> Settings:
    """
    Retorna instância singleton das configurações.
    Valida configurações na primeira chamada.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_secret_key()
    return _settings


# Exportar instância para uso direto
settings = get_settings()
