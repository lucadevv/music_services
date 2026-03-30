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
    
    async def _call_ytmusic(self, func, *args, **kwargs) -> Any:
        """
        Execute a YTMusic call using the account-specific semaphore.
        This prevents overloading a single account and improves stability.
        """
        import asyncio
        from app.core.browser_client import current_account_var
        
        account = current_account_var.get()
        if account:
            async with account.semaphore:
                return await asyncio.to_thread(func, *args, **kwargs)
        else:
            # Fallback if no account in context (should not happen with get_ytmusic)
            return await asyncio.to_thread(func, *args, **kwargs)

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
        
        # Track errors in the current browser account
        from app.core.browser_client import current_account_var
        account = current_account_var.get()
        
        # Authentication errors - usually means OAuth credentials are invalid or expired
        if any(pattern in error_msg for pattern in [
            "Expecting value", "JSONDecodeError", "line 1 column 1", "Invalid JSON"
        ]) or "JSONDecodeError" in error_type:
            if account: account.mark_error()
            return AuthenticationError(
                message="Error de autenticación con YouTube Music. Verifica las credenciales.",
                details={"operation": operation, "account": account.name if account else "unknown"}
            )
        
        # Rate limiting errors
        if any(pattern in error_msg.lower() for pattern in [
            "rate limit", "429", "too many requests", "resource_exhausted",
            "rate-limit", "rate limited", "quota exceeded"
        ]):
            if account: account.rate_limited_until = time.time() + 300 # 5 min penalty
            return RateLimitError(
                message="Límite de peticiones excedido. Intenta más tarde.",
                details={"operation": operation, "account": account.name if account else "unknown"}
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
