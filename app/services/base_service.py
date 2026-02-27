"""Base service class with common functionality."""
import logging
from typing import Any, Optional
from ytmusicapi import YTMusic

from app.core.logging_config import get_logger
from app.core.exceptions import (
    YTMusicServiceException,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ExternalServiceError,
)


class BaseService:
    """
    Base class for all YouTube Music services.
    
    Provides common error handling and logging functionality.
    """
    
    def __init__(self, ytmusic: Optional[YTMusic] = None):
        """
        Initialize the base service.
        
        Args:
            ytmusic: Optional YTMusic client instance.
        """
        self._ytmusic = ytmusic
        self._logger = get_logger(self.__class__.__module__)
    
    @property
    def ytmusic(self) -> YTMusic:
        """Get the YTMusic client."""
        if self._ytmusic is None:
            raise RuntimeError("YTMusic client not initialized")
        return self._ytmusic
    
    @ytmusic.setter
    def ytmusic(self, value: YTMusic) -> None:
        """Set the YTMusic client."""
        self._ytmusic = value
    
    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance."""
        return self._logger
    
    def _handle_ytmusic_error(
        self, 
        error: Exception, 
        operation: str
    ) -> YTMusicServiceException:
        """
        Handle ytmusicapi errors and return appropriate custom exception.
        
        This method analyzes the error and returns the most appropriate
        custom exception with a user-friendly message (in Spanish) that
        does not expose internal details.
        
        Args:
            error: The original exception from ytmusicapi.
            operation: Description of the operation being performed.
        
        Returns:
            An appropriate YTMusicServiceException subclass.
        """
        error_msg = str(error)
        error_type = type(error).__name__
        
        # Log the full error internally for debugging
        self._logger.error(
            f"YTMusic error during '{operation}': {error_type} - {error_msg}"
        )
        
        # Authentication errors - usually means browser.json is invalid or expired
        # Patterns: JSON parsing errors, empty responses, auth failures
        if any(pattern in error_msg for pattern in [
            "Expecting value", "JSONDecodeError", "line 1 column 1", "Invalid JSON"
        ]) or "JSONDecodeError" in error_type:
            return AuthenticationError(
                message="Error de autenticación con YouTube Music. Verifica las credenciales.",
                details={"operation": operation}
            )
        
        # Rate limiting errors
        # Patterns: 429 status, rate limit messages, resource exhausted
        if any(pattern in error_msg.lower() for pattern in [
            "rate limit", "429", "too many requests", "resource_exhausted",
            "rate-limit", "rate limited", "quota exceeded"
        ]):
            return RateLimitError(
                message="Límite de peticiones excedido. Intenta más tarde.",
                details={"operation": operation}
            )
        
        # Resource not found errors
        # Patterns: not found messages, does not exist
        if any(pattern in error_msg.lower() for pattern in [
            "not found", "no encontrado", "does not exist", "unable to find"
        ]):
            return ResourceNotFoundError(
                message=f"Recurso no encontrado en {operation}.",
                details={"operation": operation}
            )
        
        # Default to external service error for all other cases
        # This avoids exposing internal error details to clients
        return ExternalServiceError(
            message=f"Error en el servicio de YouTube Music durante {operation}. Intenta más tarde.",
            details={"operation": operation}
        )
    
    def _log_operation(self, operation: str, **kwargs: Any) -> None:
        """
        Log an operation with optional parameters.
        
        Args:
            operation: Name of the operation.
            **kwargs: Additional parameters to log.
        """
        params = ", ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        self._logger.debug(f"Starting {operation}" + (f" ({params})" if params else ""))
