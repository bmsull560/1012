"""Application configuration using Pydantic Settings"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import secrets as secrets_lib


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "ValueVerse Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "ValueVerse"
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets_lib.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes for production security
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    ALGORITHM: str = "HS256"
    BCRYPT_ROUNDS: int = 12
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://valueverse:valueverse@localhost:5432/valueverse",
        env="DATABASE_URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    TOGETHER_API_KEY: Optional[str] = Field(default=None, env="TOGETHER_API_KEY")
    
    # Vector Store
    PINECONE_API_KEY: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: str = Field(default="us-east-1", env="PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME: str = Field(default="valueverse", env="PINECONE_INDEX_NAME")
    
    # WebSocket
    WEBSOCKET_SECRET: str = Field(default_factory=lambda: secrets_lib.token_urlsafe(32))
    WEBSOCKET_PING_INTERVAL: int = 25
    WEBSOCKET_PING_TIMEOUT: int = 5
    WEBSOCKET_MAX_CONNECTIONS: int = 10000
    
    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        env="CELERY_RESULT_BACKEND"
    )
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get settings instance with secrets management integration"""
    settings = Settings()
    
    # In production, override with secrets from AWS Secrets Manager
    if settings.ENVIRONMENT == "production":
        try:
            from .secrets import secrets_manager
            
            # Get JWT configuration
            jwt_config = secrets_manager.get_jwt_config()
            settings.SECRET_KEY = jwt_config.get('secret_key', settings.SECRET_KEY)
            settings.ACCESS_TOKEN_EXPIRE_MINUTES = jwt_config.get('access_token_expire_minutes', 15)
            
            # Get database URL
            settings.DATABASE_URL = secrets_manager.get_database_url()
            
            # Get API keys
            api_keys = secrets_manager.get_secret("valueverse/prod/api-keys")
            settings.OPENAI_API_KEY = api_keys.get('openai_api_key')
            settings.ANTHROPIC_API_KEY = api_keys.get('anthropic_api_key')
            settings.TOGETHER_API_KEY = api_keys.get('together_api_key')
            
        except Exception as e:
            print(f"Warning: Could not load production secrets: {e}")
    
    return settings


settings = get_settings()
