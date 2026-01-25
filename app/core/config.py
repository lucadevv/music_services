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
    
    # YouTube Music Configuration
    BROWSER_JSON_PATH: str = "browser.json"
    OAUTH_JSON_PATH: Optional[str] = None
    
    # CORS Configuration
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60  # Requests per minute per IP
    RATE_LIMIT_PER_HOUR: int = 1000   # Requests per hour per IP
    
    # Caching Configuration
    CACHE_ENABLED: bool = True
    CACHE_BACKEND: str = "memory"  # "memory" or "redis"
    CACHE_TTL: int = 300  # 5 minutes default TTL
    CACHE_MAX_SIZE: int = 1000  # Max items in memory cache
    
    # Redis Configuration (if using Redis cache)
    REDIS_HOST: str = "localhost"  # Use "redis" when running in Docker Compose
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # HTTP Client Configuration
    HTTP_TIMEOUT: int = 30  # seconds
    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20
    
    # Performance
    ENABLE_COMPRESSION: bool = True
    MAX_WORKERS: int = 10  # Max concurrent workers for asyncio.to_thread
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
