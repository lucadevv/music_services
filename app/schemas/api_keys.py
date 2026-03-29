"""Authentication schemas for API keys with PostgreSQL backend."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    title: str = Field(
        ...,
        description="Título descriptivo para identificar la API key",
        min_length=1,
        max_length=100,
        examples=["Mobile App", "NestJS Backend", "Web Client"]
    )
    description: Optional[str] = Field(
        None,
        description="Descripción opcional para dar contexto sobre el uso de la key"
    )


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    key_id: str = Field(..., description="ID único de la API key (identificador interno)")
    api_key: str = Field(..., description="API key completa (solo se muestra al crear)")
    title: str = Field(..., description="Título descriptivo de la API key")
    description: Optional[str] = Field(None, description="Descripción opcional")
    enabled: bool = Field(..., description="Indica si la API key está habilitada para uso")
    created_at: datetime = Field(..., description="Fecha y hora de creación de la key")
    last_used: Optional[datetime] = Field(None, description="Última vez que se usó la key")
    is_admin: bool = Field(False, description="Indica si es una key de administrador")


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    title: Optional[str] = Field(
        None,
        description="Nuevo título para la API key",
        max_length=100
    )
    description: Optional[str] = Field(None, description="Nueva descripción")
    enabled: Optional[bool] = Field(
        None,
        description="Habilitar (true) o deshabilitar (false) la API key"
    )


class APIKeyListResponse(BaseModel):
    """Schema for listing API keys."""
    total: int = Field(..., description="Total de API keys existentes")
    keys: list[APIKeyResponse] = Field(..., description="Lista de todas las API keys")


class APIKeyVerifyResponse(BaseModel):
    """Schema for API key verification."""
    valid: bool = Field(..., description="Indica si la API key es válida")
    key_id: Optional[str] = Field(None, description="ID de la API key (si es válida)")
    title: Optional[str] = Field(None, description="Título de la API key (si es válida)")
