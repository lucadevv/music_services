"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "YouTube Music Service"
    VERSION: str = "1.0.0"
    
    BROWSER_JSON_PATH: str = "browser.json"
    OAUTH_JSON_PATH: str = "oauth.json"
    YTMUSIC_CLIENT_ID: Optional[str] = None
    YTMUSIC_CLIENT_SECRET: Optional[str] = None
    
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    CACHE_ENABLED: bool = True
    CACHE_BACKEND: str = "memory"
    CACHE_TTL: int = 300
    CACHE_MAX_SIZE: int = 1000
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    HTTP_TIMEOUT: int = 30
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20
    
    ENABLE_COMPRESSION: bool = True
    MAX_WORKERS: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
