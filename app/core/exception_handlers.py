"""Global exception handlers for FastAPI application.

This module provides centralized exception handling that:
- Converts custom exceptions to proper HTTP responses
- Sanitizes error messages to avoid exposing internals
- Logs errors for debugging while returning safe messages to clients
- Provides consistent error response format across all endpoints
"""
from typing import Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import YTMusicServiceException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def ytmusic_exception_handler(
    request: Request, 
    exc: YTMusicServiceException
) -> JSONResponse:
    """Handler for custom YTMusic exceptions.
    
    Converts YTMusicServiceException and its subclasses into
    properly formatted JSON responses with appropriate HTTP status codes.
    
    Args:
        request: The FastAPI request object.
        exc: The raised YTMusicServiceException.
    
    Returns:
        JSONResponse with error details and appropriate status code.
    """
    # Log the error with context
    logger.warning(
        f"Service error on {request.method} {request.url.path}: "
        f"[{exc.error_code}] {exc.message}"
    )
    
    # Build response
    response_content: Dict[str, Any] = {
        "error": True,
        "error_code": exc.error_code,
        "message": exc.message,
    }
    
    # Include details if present (already sanitized in exception)
    if exc.details:
        response_content["details"] = exc.details
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """Handler for FastAPI request validation errors.
    
    Converts Pydantic validation errors into user-friendly
    error responses in Spanish.
    
    Args:
        request: The FastAPI request object.
        exc: The RequestValidationError from FastAPI.
    
    Returns:
        JSONResponse with validation error details.
    """
    # Extract and format validation errors
    errors = exc.errors()
    formatted_errors = []
    
    for error in errors:
        formatted_error = {
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": _translate_validation_message(error.get("msg", "")),
            "type": error.get("type", "unknown")
        }
        formatted_errors.append(formatted_error)
    
    logger.debug(
        f"Validation error on {request.method} {request.url.path}: "
        f"{len(formatted_errors)} errors"
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "error_code": "VALIDATION_ERROR",
            "message": "Error de validación en los parámetros de la petición",
            "details": {
                "errors": formatted_errors,
                "count": len(formatted_errors)
            }
        }
    )


async def generic_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """Handler for unexpected/unhandled exceptions.
    
    Catches any exception not handled by other handlers.
    Logs the full error internally but returns a generic message
    to avoid exposing internal details to clients.
    
    Args:
        request: The FastAPI request object.
        exc: The unhandled exception.
    
    Returns:
        JSONResponse with generic error message (500 status).
    """
    # Log the full error with traceback for debugging
    logger.error(
        f"Unexpected error on {request.method} {request.url.path}: "
        f"{type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    
    # Return generic message to client (don't expose internals)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "INTERNAL_ERROR",
            "message": "Ha ocurrido un error interno. Por favor intenta más tarde.",
            "details": None
        }
    )


def _translate_validation_message(msg: str) -> str:
    """Translate common validation messages to Spanish.
    
    Args:
        msg: Original English validation message.
    
    Returns:
        Translated Spanish message or original if no translation.
    """
    translations = {
        "field required": "campo requerido",
        "none is not an allowed value": "valor nulo no permitido",
        "value is not a valid integer": "valor no es un entero válido",
        "value is not a valid float": "valor no es un número decimal válido",
        "value is not a valid boolean": "valor no es un booleano válido",
        "value is not a valid email": "valor no es un email válido",
        "value is not a valid url": "valor no es una URL válida",
        "string does not match regex": "formato no válido",
        "ensure this value is greater than or equal to": "el valor debe ser mayor o igual a",
        "ensure this value is less than or equal to": "el valor debe ser menor o igual a",
        "ensure this value is greater than": "el valor debe ser mayor a",
        "ensure this value is less than": "el valor debe ser menor a",
        "string length": "longitud de texto",
        "list should have at least": "la lista debe tener al menos",
        "list should have at most": "la lista debe tener como máximo",
    }
    
    msg_lower = msg.lower()
    for eng, spa in translations.items():
        if eng in msg_lower:
            return spa
    
    return msg


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app.
    
    This function should be called during app initialization
    to set up all global exception handlers.
    
    Args:
        app: The FastAPI application instance.
    """
    # Register custom exception handlers
    app.add_exception_handler(YTMusicServiceException, ytmusic_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Note: Uncomment to catch ALL unhandled exceptions (useful in production)
    # app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
