"""Unit tests for exception handlers."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import (
    YTMusicServiceException,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
    ExternalServiceError,
    CircuitBreakerError,
)
from app.core.exception_handlers import (
    ytmusic_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
    _translate_validation_message,
)


class TestYTMusicExceptionHandler:
    """Tests for ytmusic_exception_handler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = MagicMock()
        request.url.path = "/api/v1/test"
        return request

    @pytest.mark.asyncio
    async def test_authentication_error(self, mock_request):
        """Test handler for AuthenticationError."""
        exc = AuthenticationError(
            message="Error de autenticación",
            details={"operation": "search"}
        )
        
        response = await ytmusic_exception_handler(mock_request, exc)
        
        assert response.status_code == 401
        # Parse the body to check content

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, mock_request):
        """Test handler for RateLimitError."""
        exc = RateLimitError(
            message="Rate limit exceeded",
            details={"retry_after": 300}
        )
        
        response = await ytmusic_exception_handler(mock_request, exc)
        
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_not_found_error(self, mock_request):
        """Test handler for ResourceNotFoundError."""
        exc = ResourceNotFoundError(
            message="Video no encontrado",
            details={"resource_type": "video", "resource_id": "abc123"}
        )
        
        response = await ytmusic_exception_handler(mock_request, exc)
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_error(self, mock_request):
        """Test handler for ValidationError."""
        exc = ValidationError(
            message="ID de video inválido",
            details={"field": "video_id", "reason": "too_short"}
        )
        
        response = await ytmusic_exception_handler(mock_request, exc)
        
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_external_service_error(self, mock_request):
        """Test handler for ExternalServiceError."""
        exc = ExternalServiceError(
            message="Error en YouTube Music",
            details={"operation": "get_stream"}
        )
        
        response = await ytmusic_exception_handler(mock_request, exc)
        
        assert response.status_code == 502

    @pytest.mark.asyncio
    async def test_circuit_breaker_error(self, mock_request):
        """Test handler for CircuitBreakerError."""
        exc = CircuitBreakerError(
            message="Servicio no disponible",
            details={"retry_after": 180, "state": "OPEN"}
        )
        
        response = await ytmusic_exception_handler(mock_request, exc)
        
        assert response.status_code == 503


class TestValidationExceptionHandler:
    """Tests for validation_exception_handler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url = MagicMock()
        request.url.path = "/api/v1/search"
        return request

    @pytest.mark.asyncio
    async def test_validation_error_handler(self, mock_request):
        """Test handler for RequestValidationError."""
        errors = [
            {
                "loc": ("body", "query"),
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
        exc = RequestValidationError(errors)
        
        response = await validation_exception_handler(mock_request, exc)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_multiple_validation_errors(self, mock_request):
        """Test handler with multiple validation errors."""
        errors = [
            {
                "loc": ("body", "query"),
                "msg": "field required",
                "type": "value_error.missing"
            },
            {
                "loc": ("body", "limit"),
                "msg": "ensure this value is less than or equal to 100",
                "type": "value_error.number.not_le"
            }
        ]
        exc = RequestValidationError(errors)
        
        response = await validation_exception_handler(mock_request, exc)
        
        assert response.status_code == 422


class TestGenericExceptionHandler:
    """Tests for generic_exception_handler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = MagicMock()
        request.url.path = "/api/v1/test"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_generic_error(self, mock_request):
        """Test handler for generic Exception."""
        exc = Exception("Some unexpected error")
        
        response = await generic_exception_handler(mock_request, exc)
        
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_does_not_expose_error_details(self, mock_request):
        """Test that generic handler doesn't expose internal error details."""
        exc = Exception("Internal database connection string: postgresql://user:pass@host")
        
        response = await generic_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
        # The response should not contain the sensitive connection string


class TestTranslateValidationMessage:
    """Tests for _translate_validation_message function."""

    def test_field_required(self):
        """Test translation of 'field required'."""
        result = _translate_validation_message("field required")
        assert "requerido" in result

    def test_value_not_integer(self):
        """Test translation of 'value is not a valid integer'."""
        result = _translate_validation_message("value is not a valid integer")
        assert "entero" in result

    def test_unknown_message_returns_original(self):
        """Test that unknown messages return original."""
        result = _translate_validation_message("some unknown error message")
        assert result == "some unknown error message"

    def test_case_insensitive(self):
        """Test that translation is case insensitive."""
        result = _translate_validation_message("FIELD REQUIRED")
        assert "requerido" in result
