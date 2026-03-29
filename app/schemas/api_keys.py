"""API Key schemas for authentication."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    title: str = Field(...,        description="Título descriptivo para identificar la API key",
        min_length=1,
        max_length=100,
        examples=["Mobile App", "NestJS Backend", "Admin Panel"],
    )
    api_key: Optional[str] = Field(
        None,
        description="API key personalizada (opcional, se genera automáticamente si no se proporcion)",
        min_length=32,
        max_length=64,
    )


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    key_id: str = Field(...,        description="ID único de la API key",
        examples=["abc123def456"],
    )
    api_key: str = Field(...,
        description="API key generada",
        examples=["sk_live_abc123..."],
    )
    title: str = Field(...,
        description="Título descriptivo",
        examples=["Mobile App"],
    )
    enabled: bool = Field(...,        description="Si la API key está habilitada",
        examples=[True],
    )
    created_at: str = Field(...,        description="Fecha de creación (ISO 8601)",
        examples=["2026-03-29T10:00:00Z"],
    )
    last_used: Optional[str] = Field(
        None,
        description="Última vez que se usó (ISO 8601)",
        examples=["2026-03-29T15:30:00Z"],
    )
    is_master: bool = Field(
        False,
        description="Si es la API key maestra",
        examples=[False],
    )


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    title: Optional[str] = Field(
        None,
        description="Nuevo título",
        min_length=1,
        max_length=100,
    )
    enabled: Optional[bool] = Field(
        None,
        description="Habilitar/inhabilitar",
        examples=[True, False],
    )


class APIKeyListResponse(BaseModel):
    """Schema for listing API keys."""
    total: int = Field(...,        description="Total de API keys",
        examples=[5],
    )
    keys: list[APIKeyResponse] = Field(...,        description="Lista de API keys",
    )


class APIKeyVerifyResponse(BaseModel):
    """Schema for API key verification."""
    valid: bool = Field(...,        description="Si la API key es válida",
        examples=[True],
    )
    key_id: Optional[str] = Field(
        None,
        description="ID de la API key (si es válida)",
        examples=["abc123def456"],
    )
    title: Optional[str] = Field(
        None,
        description="Título de la API key",
        examples=["Mobile App"],
    )
