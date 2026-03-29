"""Authentication schemas for API keys with PostgreSQL backend."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


from app.core.auth import generate_api_key, hash_api_key


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    title: str = Field(..., description="Título descriptivo", min_length=1, max_length=100, examples=["Mobile App", "NestJS Backend"],
    )
    description: Optional[str] = Field(None, description="Descripción opcional")


    )


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    key_id: str = Field(..., description="ID único de la API key")
    api_key: str = Field(..., description="API key generada")
    title: str = Field(..., description="Título descriptivo")
    description: Optional[str] = Field(None, description="Descripción opcional")
    enabled: bool = Field(..., description="Si la API key está habilitada")
    created_at: datetime = Field(..., description="Fecha de creación")
    last_used: Optional[datetime] = Field(None, description="Última vez que se usó")
    is_admin: bool = Field(False, description="Si es admin")
    description: Optional[str] = Field(None, description="Descripción opcional")


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    title: Optional[str] = Field(None, description="Nuevo título")
    description: Optional[str] = Field(None, description="Nueva descripción")
    enabled: Optional[bool] = Field(None, description="Habilitar/inhabilitar")


class APIKeyListResponse(BaseModel):
    """Schema for listing API keys."""
    total: int = Field(..., description="Total de API keys")
    keys: list[APIKeyResponse] = Field(..., description="Lista de API keys")


class APIKeyVerifyResponse(BaseModel):
    """Schema for API key verification."""
    valid: bool = Field(..., description="Si la API key es válida")
    key_id: Optional[str] = Field(None, description="ID de la API key (si es válida)")
    title: Optional[str] = Field(None, description="Título de la API key")
