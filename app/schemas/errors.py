"""Error response schemas for API documentation.

This module defines Pydantic models for error responses to ensure
consistent documentation in OpenAPI/Swagger.
"""
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field


class ErrorDetailItem(BaseModel):
    """Single error detail item for validation errors."""
    
    field: str = Field(
        ..., 
        description="Field that caused the error",
        examples=["query", "video_id", "limit"]
    )
    message: str = Field(
        ..., 
        description="Human-readable error message",
        examples=["campo requerido", "valor inválido"]
    )
    type: Optional[str] = Field(
        None, 
        description="Error type identifier",
        examples=["value_error.missing", "type_error.integer"]
    )


class ErrorDetails(BaseModel):
    """Container for error details."""
    
    errors: Optional[List[ErrorDetailItem]] = Field(
        None, 
        description="List of individual errors (for validation errors)"
    )
    count: Optional[int] = Field(
        None, 
        description="Number of errors"
    )
    operation: Optional[str] = Field(
        None, 
        description="Operation that caused the error"
    )
    field: Optional[str] = Field(
        None, 
        description="Field that caused the error"
    )
    reason: Optional[str] = Field(
        None, 
        description="Reason for the error"
    )
    retry_after: Optional[int] = Field(
        None, 
        description="Seconds to wait before retrying"
    )
    resource_type: Optional[str] = Field(
        None, 
        description="Type of resource that was not found"
    )
    resource_id: Optional[str] = Field(
        None, 
        description="ID of resource that was not found"
    )
    state: Optional[str] = Field(
        None, 
        description="State (e.g., circuit breaker state)",
        examples=["OPEN", "CLOSED", "HALF_OPEN"]
    )
    hint: Optional[str] = Field(
        None, 
        description="Hint for resolving the error"
    )


class ErrorResponse(BaseModel):
    """Standard error response schema for all API errors.
    
    This schema is used consistently across all endpoints to provide
    a predictable error format for clients.
    
    Attributes:
        error: Always True for error responses.
        error_code: Machine-readable error code for programmatic handling.
        message: Human-readable error message in Spanish.
        details: Optional additional details about the error.
    """
    
    error: bool = Field(
        True, 
        description="Always True for error responses"
    )
    error_code: str = Field(
        ..., 
        description="Machine-readable error code",
        examples=[
            "VALIDATION_ERROR",
            "AUTHENTICATION_ERROR",
            "RATE_LIMIT_ERROR",
            "NOT_FOUND",
            "EXTERNAL_SERVICE_ERROR",
            "SERVICE_UNAVAILABLE",
            "INTERNAL_ERROR"
        ]
    )
    message: str = Field(
        ..., 
        description="Human-readable error message in Spanish",
        examples=[
            "Error de validación en los parámetros de la petición",
            "Error de autenticación con YouTube Music",
            "Límite de peticiones excedido. Intenta más tarde.",
            "Recurso no encontrado",
            "Error en el servicio de YouTube Music",
            "Servicio temporalmente no disponible"
        ]
    )
    details: Optional[ErrorDetails] = Field(
        None, 
        description="Additional error details (structure varies by error type)"
    )


# Specific error response examples for OpenAPI documentation

VALIDATION_ERROR_EXAMPLE = {
    "error": True,
    "error_code": "VALIDATION_ERROR",
    "message": "Error de validación en 'video_id': ID de video inválido. Debe tener exactamente 11 caracteres.",
    "details": {
        "field": "video_id",
        "reason": "invalid_length",
        "expected_length": 11,
        "actual_length": 5
    }
}

AUTHENTICATION_ERROR_EXAMPLE = {
    "error": True,
    "error_code": "AUTHENTICATION_ERROR",
    "message": "Error de autenticación con YouTube Music. Verifica las credenciales.",
    "details": {
        "operation": "search",
        "hint": "Check server logs for details"
    }
}

RATE_LIMIT_ERROR_EXAMPLE = {
    "error": True,
    "error_code": "RATE_LIMIT_ERROR",
    "message": "Límite de peticiones excedido. Intenta más tarde.",
    "details": {
        "operation": "get_stream",
        "retry_after": 300
    }
}

NOT_FOUND_ERROR_EXAMPLE = {
    "error": True,
    "error_code": "NOT_FOUND",
    "message": "Video no encontrado.",
    "details": {
        "resource_type": "video",
        "resource_id": "rMbATaj7Il8"
    }
}

EXTERNAL_SERVICE_ERROR_EXAMPLE = {
    "error": True,
    "error_code": "EXTERNAL_SERVICE_ERROR",
    "message": "Error en YouTube Music durante get_stream. Intenta más tarde.",
    "details": {
        "operation": "get_stream",
        "service": "YouTube Music"
    }
}

SERVICE_UNAVAILABLE_ERROR_EXAMPLE = {
    "error": True,
    "error_code": "SERVICE_UNAVAILABLE",
    "message": "Servicio temporalmente no disponible debido a sobrecarga.",
    "details": {
        "retry_after": 180,
        "state": "OPEN"
    }
}

INTERNAL_ERROR_EXAMPLE = {
    "error": True,
    "error_code": "INTERNAL_ERROR",
    "message": "Ha ocurrido un error interno. Por favor intenta más tarde.",
    "details": None
}


# Common response schemas for OpenAPI

COMMON_ERROR_RESPONSES = {
    400: {
        "description": "Bad Request - Error de validación",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": VALIDATION_ERROR_EXAMPLE
            }
        }
    },
    401: {
        "description": "Unauthorized - Error de autenticación",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": AUTHENTICATION_ERROR_EXAMPLE
            }
        }
    },
    404: {
        "description": "Not Found - Recurso no encontrado",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": NOT_FOUND_ERROR_EXAMPLE
            }
        }
    },
    429: {
        "description": "Too Many Requests - Rate limit excedido",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": RATE_LIMIT_ERROR_EXAMPLE
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": INTERNAL_ERROR_EXAMPLE
            }
        }
    },
    502: {
        "description": "Bad Gateway - Error de servicio externo",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": EXTERNAL_SERVICE_ERROR_EXAMPLE
            }
        }
    },
    503: {
        "description": "Service Unavailable - Servicio no disponible",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": SERVICE_UNAVAILABLE_ERROR_EXAMPLE
            }
        }
    }
}
