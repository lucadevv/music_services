"""Schemas for browser authentication endpoints."""
from typing import Optional, List
from pydantic import BaseModel, Field


class BrowserAddResponse(BaseModel):
    """Response when adding a browser account."""

    success: bool = Field(..., description="Indica si la cuenta fue agregada exitosamente")
    account_name: str = Field(..., description="Nombre de la cuenta agregada")
    message: str = Field(..., description="Mensaje legible para humanos")


class BrowserAccountInfo(BaseModel):
    """Information about a browser account."""

    name: str = Field(..., description="Nombre de la cuenta")
    available: bool = Field(..., description="Indica si la cuenta está disponible para uso")
    error_count: int = Field(..., description="Número de errores consecutivos")
    rate_limited_until: Optional[float] = Field(None, description="Timestamp UNIX cuando expira el rate limit")
    last_used: float = Field(..., description="Timestamp UNIX del último uso")


class BrowserListResponse(BaseModel):
    """Response listing all browser accounts."""

    total: int = Field(..., description="Total de cuentas registradas")
    available: int = Field(..., description="Número de cuentas disponibles")
    accounts: List[BrowserAccountInfo] = Field(..., description="Lista de todas las cuentas")


class BrowserTestResponse(BaseModel):
    """Response for authentication test."""

    success: bool = Field(..., description="Indica si la autenticación funciona")
    message: str = Field(..., description="Mensaje legible para humanos")
    account_used: Optional[str] = Field(None, description="Cuenta usada para la prueba")


class AuthStatusResponse(BaseModel):
    """Response for authentication status check."""

    authenticated: bool = Field(..., description="Indica si el servicio está autenticado")
    method: str = Field(..., description="Método de autenticación (browser)")
    total_accounts: int = Field(..., description="Total de cuentas registradas")
    available_accounts: int = Field(..., description="Número de cuentas disponibles")
    accounts: List[BrowserAccountInfo] = Field(default_factory=list, description="Lista de cuentas")
