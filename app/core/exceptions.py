"""Custom exceptions for YouTube Music service.

This module defines a hierarchy of exceptions for proper error handling:
- YTMusicServiceException: Base exception for all service errors
- AuthenticationError: Authentication/credential issues (401)
- RateLimitError: Rate limiting from YouTube (429)
- ResourceNotFoundError: Resource not found (404)
- ValidationError: Input validation errors (400)
- ExternalServiceError: External service failures (502)
- CircuitBreakerError: Circuit breaker open (503)
"""
from typing import Optional, Dict, Any


class YTMusicServiceException(Exception):
    """Base exception for YouTube Music service errors.
    
    All custom exceptions inherit from this class to allow
    catching all service-specific errors with a single except clause.
    
    Attributes:
        status_code: HTTP status code to return.
        error_code: Machine-readable error code for programmatic handling.
        message: Human-readable error message (in Spanish).
        details: Optional additional details about the error.
    """
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize the exception.
        
        Args:
            message: Human-readable error message.
            details: Optional dictionary with additional error details.
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response.
        
        Returns:
            Dictionary representation of the error.
        """
        result = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class AuthenticationError(YTMusicServiceException):
    """Error de autenticación con YouTube Music.
    
    Raised when:
    - browser.json is invalid or expired
    - Credentials are malformed
    - Session has expired
    - YouTube returns authentication errors
    """
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"


class RateLimitError(YTMusicServiceException):
    """Rate limit excedido en YouTube Music.
    
    Raised when:
    - YouTube API returns 429 status
    - Rate limit messages detected in responses
    - Too many requests in short time period
    """
    status_code = 429
    error_code = "RATE_LIMIT_ERROR"


class ResourceNotFoundError(YTMusicServiceException):
    """Recurso no encontrado en YouTube Music.
    
    Raised when:
    - Video, album, artist, playlist doesn't exist
    - Resource has been removed
    - Invalid ID provided
    """
    status_code = 404
    error_code = "NOT_FOUND"


class ValidationError(YTMusicServiceException):
    """Error de validación de input.
    
    Raised when:
    - Required parameter is missing
    - Parameter format is invalid
    - Parameter value is out of allowed range
    - Video ID format is incorrect
    """
    status_code = 400
    error_code = "VALIDATION_ERROR"


class ExternalServiceError(YTMusicServiceException):
    """Error de servicio externo (YouTube, yt-dlp).
    
    Raised when:
    - YouTube API returns unexpected errors
    - yt-dlp fails to extract stream
    - Network connectivity issues
    - Timeout from external services
    """
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"


class CircuitBreakerError(YTMusicServiceException):
    """Circuit breaker abierto - servicio no disponible.
    
    Raised when:
    - Circuit breaker is in OPEN state
    - Too many recent failures
    - Service is temporarily unavailable
    """
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"


# Convenience functions for creating common exceptions

def raise_authentication_error(operation: str, original_error: Optional[str] = None) -> None:
    """Raise an AuthenticationError with standardized message.
    
    Args:
        operation: The operation that failed.
        original_error: Optional original error message (not exposed to client).
    
    Raises:
        AuthenticationError: Always raised.
    """
    details = {"operation": operation}
    if original_error:
        # Log internally but don't expose to client
        details["hint"] = "Check server logs for details"
    
    raise AuthenticationError(
        message="Error de autenticación con YouTube Music. Verifica las credenciales.",
        details=details
    )


def raise_rate_limit_error(operation: str, retry_after: Optional[int] = None) -> None:
    """Raise a RateLimitError with standardized message.
    
    Args:
        operation: The operation that was rate limited.
        retry_after: Optional seconds to wait before retrying.
    
    Raises:
        RateLimitError: Always raised.
    """
    details = {"operation": operation}
    if retry_after:
        details["retry_after"] = retry_after
    
    raise RateLimitError(
        message="Límite de peticiones excedido. Intenta más tarde.",
        details=details
    )


def raise_not_found_error(resource_type: str, resource_id: str) -> None:
    """Raise a ResourceNotFoundError with standardized message.
    
    Args:
        resource_type: Type of resource (video, album, artist, etc.).
        resource_id: ID of the resource that was not found.
    
    Raises:
        ResourceNotFoundError: Always raised.
    """
    raise ResourceNotFoundError(
        message=f"{resource_type.capitalize()} no encontrado.",
        details={
            "resource_type": resource_type,
            "resource_id": resource_id
        }
    )


def raise_validation_error(field: str, reason: str, value: Optional[str] = None) -> None:
    """Raise a ValidationError with standardized message.
    
    Args:
        field: The field that failed validation.
        reason: Human-readable reason for the failure.
        value: Optional the invalid value (sanitized).
    
    Raises:
        ValidationError: Always raised.
    """
    details = {"field": field, "reason": reason}
    if value:
        # Truncate to avoid exposing too much data
        details["value"] = value[:50] if len(value) > 50 else value
    
    raise ValidationError(
        message=f"Error de validación en '{field}': {reason}",
        details=details
    )


def raise_external_service_error(operation: str, service: str = "YouTube Music") -> None:
    """Raise an ExternalServiceError with standardized message.
    
    Args:
        operation: The operation that failed.
        service: The external service that failed.
    
    Raises:
        ExternalServiceError: Always raised.
    """
    raise ExternalServiceError(
        message=f"Error en {service} durante {operation}. Intenta más tarde.",
        details={"operation": operation, "service": service}
    )


def raise_circuit_breaker_error(remaining_seconds: int) -> None:
    """Raise a CircuitBreakerError with standardized message.
    
    Args:
        remaining_seconds: Seconds until circuit breaker resets.
    
    Raises:
        CircuitBreakerError: Always raised.
    """
    raise CircuitBreakerError(
        message="Servicio temporalmente no disponible debido a sobrecarga.",
        details={
            "retry_after": remaining_seconds,
            "state": "OPEN"
        }
    )
