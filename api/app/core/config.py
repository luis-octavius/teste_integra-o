"""
Configurações da aplicação
"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Aplicação
    APP_NAME: str = "ANS Analytics API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Banco de dados
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ans_analytics"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    # Cache
    CACHE_TTL_SECONDS: int = 300
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

# Instância global das configurações
settings = Settings()

# Carregar variáveis de ambiente
def load_settings():
    return Settings()

# Para usar: from app.core.config import settings
