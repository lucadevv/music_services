"""Unit tests for custom exceptions."""
import pytest
from app.core.exceptions import (
    YTMusicServiceException,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
    ExternalServiceError,
    CircuitBreakerError,
    raise_authentication_error,
    raise_rate_limit_error,
    raise_not_found_error,
    raise_validation_error,
    raise_external_service_error,
    raise_circuit_breaker_error,
)


class TestYTMusicServiceException:
    """Tests for base YTMusicServiceException."""

    def test_default_values(self):
        """Test default status_code and error_code."""
        exc = YTMusicServiceException("Test error")
        
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.message == "Test error"
        assert exc.details == {}

    def test_custom_message(self):
        """Test with custom message."""
        exc = YTMusicServiceException("Custom error message")
        
        assert exc.message == "Custom error message"

    def test_details_dict(self):
        """Test with details dictionary."""
        exc = YTMusicServiceException(
            "Test error",
            details={"key": "value", "operation": "test"}
        )
        
        assert exc.details == {"key": "value", "operation": "test"}

    def test_to_dict_without_details(self):
        """Test to_dict without details."""
        exc = YTMusicServiceException("Test error")
        result = exc.to_dict()
        
        assert result["error"] is True
        assert result["error_code"] == "INTERNAL_ERROR"
        assert result["message"] == "Test error"
        assert "details" not in result

    def test_to_dict_with_details(self):
        """Test to_dict with details."""
        exc = YTMusicServiceException(
            "Test error",
            details={"key": "value"}
        )
        result = exc.to_dict()
        
        assert result["error"] is True
        assert result["details"] == {"key": "value"}


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_status_code(self):
        """Test correct status code."""
        exc = AuthenticationError("Auth failed")
        assert exc.status_code == 401

    def test_error_code(self):
        """Test correct error code."""
        exc = AuthenticationError("Auth failed")
        assert exc.error_code == "AUTHENTICATION_ERROR"


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_status_code(self):
        """Test correct status code."""
        exc = RateLimitError("Rate limited")
        assert exc.status_code == 429

    def test_error_code(self):
        """Test correct error code."""
        exc = RateLimitError("Rate limited")
        assert exc.error_code == "RATE_LIMIT_ERROR"


class TestResourceNotFoundError:
    """Tests for ResourceNotFoundError."""

    def test_status_code(self):
        """Test correct status code."""
        exc = ResourceNotFoundError("Not found")
        assert exc.status_code == 404

    def test_error_code(self):
        """Test correct error code."""
        exc = ResourceNotFoundError("Not found")
        assert exc.error_code == "NOT_FOUND"


class TestValidationError:
    """Tests for ValidationError."""

    def test_status_code(self):
        """Test correct status code."""
        exc = ValidationError("Invalid input")
        assert exc.status_code == 400

    def test_error_code(self):
        """Test correct error code."""
        exc = ValidationError("Invalid input")
        assert exc.error_code == "VALIDATION_ERROR"


class TestExternalServiceError:
    """Tests for ExternalServiceError."""

    def test_status_code(self):
        """Test correct status code."""
        exc = ExternalServiceError("External failed")
        assert exc.status_code == 502

    def test_error_code(self):
        """Test correct error code."""
        exc = ExternalServiceError("External failed")
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"


class TestCircuitBreakerError:
    """Tests for CircuitBreakerError."""

    def test_status_code(self):
        """Test correct status code."""
        exc = CircuitBreakerError("Service unavailable")
        assert exc.status_code == 503

    def test_error_code(self):
        """Test correct error code."""
        exc = CircuitBreakerError("Service unavailable")
        assert exc.error_code == "SERVICE_UNAVAILABLE"


class TestConvenienceFunctions:
    """Tests for convenience raise functions."""

    def test_raise_authentication_error(self):
        """Test raise_authentication_error function."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise_authentication_error("search", "original error")
        
        exc = exc_info.value
        assert exc.status_code == 401
        assert exc.details["operation"] == "search"

    def test_raise_rate_limit_error(self):
        """Test raise_rate_limit_error function."""
        with pytest.raises(RateLimitError) as exc_info:
            raise_rate_limit_error("get_stream", retry_after=300)
        
        exc = exc_info.value
        assert exc.status_code == 429
        assert exc.details["operation"] == "get_stream"
        assert exc.details["retry_after"] == 300

    def test_raise_not_found_error(self):
        """Test raise_not_found_error function."""
        with pytest.raises(ResourceNotFoundError) as exc_info:
            raise_not_found_error("video", "abc123")
        
        exc = exc_info.value
        assert exc.status_code == 404
        assert exc.details["resource_type"] == "video"
        assert exc.details["resource_id"] == "abc123"

    def test_raise_validation_error(self):
        """Test raise_validation_error function."""
        with pytest.raises(ValidationError) as exc_info:
            raise_validation_error("video_id", "must be 11 characters", "short")
        
        exc = exc_info.value
        assert exc.status_code == 400
        assert exc.details["field"] == "video_id"
        assert exc.details["reason"] == "must be 11 characters"

    def test_raise_validation_error_truncates_long_value(self):
        """Test that validation error truncates long values."""
        with pytest.raises(ValidationError) as exc_info:
            raise_validation_error("field", "reason", "x" * 100)
        
        exc = exc_info.value
        assert len(exc.details["value"]) == 50

    def test_raise_external_service_error(self):
        """Test raise_external_service_error function."""
        with pytest.raises(ExternalServiceError) as exc_info:
            raise_external_service_error("get_stream", "YouTube Music")
        
        exc = exc_info.value
        assert exc.status_code == 502
        assert exc.details["operation"] == "get_stream"
        assert exc.details["service"] == "YouTube Music"

    def test_raise_circuit_breaker_error(self):
        """Test raise_circuit_breaker_error function."""
        with pytest.raises(CircuitBreakerError) as exc_info:
            raise_circuit_breaker_error(180)
        
        exc = exc_info.value
        assert exc.status_code == 503
        assert exc.details["retry_after"] == 180
        assert exc.details["state"] == "OPEN"


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from YTMusicServiceException."""
        exceptions = [
            AuthenticationError("test"),
            RateLimitError("test"),
            ResourceNotFoundError("test"),
            ValidationError("test"),
            ExternalServiceError("test"),
            CircuitBreakerError("test"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, YTMusicServiceException)
            assert isinstance(exc, Exception)

    def test_can_catch_all_with_base_exception(self):
        """Test that all custom exceptions can be caught with base class."""
        exceptions_to_raise = [
            AuthenticationError("auth"),
            RateLimitError("rate"),
            ResourceNotFoundError("not found"),
            ValidationError("validation"),
            ExternalServiceError("external"),
            CircuitBreakerError("circuit"),
        ]
        
        for exc in exceptions_to_raise:
            try:
                raise exc
            except YTMusicServiceException as e:
                assert e.message == exc.message
