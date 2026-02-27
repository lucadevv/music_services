"""Unit tests for BaseService."""
import pytest
from unittest.mock import MagicMock, patch

from app.services.base_service import BaseService
from app.core.exceptions import (
    YTMusicServiceException,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ExternalServiceError,
)


class TestBaseService:
    """Test cases for BaseService class."""

    def test_init_with_ytmusic(self, mock_ytmusic):
        """Test initialization with YTMusic client."""
        service = BaseService(mock_ytmusic)
        
        assert service._ytmusic == mock_ytmusic

    def test_init_without_ytmusic(self):
        """Test initialization without YTMusic client."""
        service = BaseService()
        
        assert service._ytmusic is None

    def test_ytmusic_property_returns_client(self, mock_ytmusic):
        """Test ytmusic property returns the client when set."""
        service = BaseService(mock_ytmusic)
        
        assert service.ytmusic == mock_ytmusic

    def test_ytmusic_property_raises_when_not_set(self):
        """Test ytmusic property raises RuntimeError when not set."""
        service = BaseService()
        
        with pytest.raises(RuntimeError, match="YTMusic client not initialized"):
            _ = service.ytmusic

    def test_ytmusic_setter(self, mock_ytmusic):
        """Test ytmusic setter updates the client."""
        service = BaseService()
        
        service.ytmusic = mock_ytmusic
        
        assert service._ytmusic == mock_ytmusic

    def test_logger_property(self, mock_ytmusic):
        """Test logger property returns a logger."""
        service = BaseService(mock_ytmusic)
        
        assert service.logger is not None
        assert hasattr(service.logger, 'info')
        assert hasattr(service.logger, 'error')
        assert hasattr(service.logger, 'debug')

    def test_log_operation_with_params(self, mock_ytmusic):
        """Test _log_operation with parameters."""
        service = BaseService(mock_ytmusic)
        
        # Should not raise any error
        service._log_operation("test_op", param1="value1", param2="value2")

    def test_log_operation_without_params(self, mock_ytmusic):
        """Test _log_operation without parameters."""
        service = BaseService(mock_ytmusic)
        
        # Should not raise any error
        service._log_operation("test_op")

    def test_log_operation_filters_none_params(self, mock_ytmusic):
        """Test that _log_operation filters out None parameters."""
        service = BaseService(mock_ytmusic)
        
        # Should not raise any error
        service._log_operation("test_op", param1="value1", param2=None)


class TestBaseServiceErrorHandling:
    """Test error handling for BaseService using custom exceptions."""

    @pytest.mark.parametrize("error_msg,expected_exception", [
        # Authentication errors
        ("Expecting value: line 1 column 1", AuthenticationError),
        ("JSONDecodeError: Expecting value", AuthenticationError),
        ("Invalid JSON", AuthenticationError),
        # Rate limiting
        ("Rate limit exceeded 429", RateLimitError),
        ("429 Too Many Requests", RateLimitError),
        ("rate limit hit", RateLimitError),
        ("rate-limit exceeded", RateLimitError),
        ("resource_exhausted", RateLimitError),
        # Not found
        ("not found", ResourceNotFoundError),
        ("does not exist", ResourceNotFoundError),
        ("unable to find resource", ResourceNotFoundError),
    ])
    def test_handle_ytmusic_error_returns_correct_exception(
        self, mock_ytmusic, error_msg, expected_exception
    ):
        """Test error handling returns correct exception type."""
        service = BaseService(mock_ytmusic)
        error = Exception(error_msg)
        
        result = service._handle_ytmusic_error(error, "test operation")
        
        assert isinstance(result, expected_exception)
        assert isinstance(result, YTMusicServiceException)
        assert result.status_code == expected_exception.status_code
        assert result.error_code == expected_exception.error_code

    def test_handle_ytmusic_error_default_to_external_service(self, mock_ytmusic):
        """Test that unknown errors default to ExternalServiceError."""
        service = BaseService(mock_ytmusic)
        error = Exception("Some random unknown error")
        
        result = service._handle_ytmusic_error(error, "test")
        
        assert isinstance(result, ExternalServiceError)
        assert result.status_code == 502
        assert result.error_code == "EXTERNAL_SERVICE_ERROR"

    def test_handle_ytmusic_error_includes_operation_in_details(self, mock_ytmusic):
        """Test that error handler includes operation in details."""
        service = BaseService(mock_ytmusic)
        error = Exception("Test error")
        
        result = service._handle_ytmusic_error(error, "custom operation")
        
        assert "operation" in result.details
        assert result.details["operation"] == "custom operation"

    def test_handle_ytmusic_error_json_decode_type(self, mock_ytmusic):
        """Test error handling when error type is JSONDecodeError."""
        import json
        
        service = BaseService(mock_ytmusic)
        
        # Create a JSONDecodeError
        try:
            json.loads("invalid json")
        except json.JSONDecodeError as e:
            result = service._handle_ytmusic_error(e, "parse response")
            
            assert isinstance(result, AuthenticationError)
            assert result.status_code == 401

    def test_handle_error_with_empty_message(self, mock_ytmusic):
        """Test error handling with empty error message."""
        service = BaseService(mock_ytmusic)
        error = Exception("")
        
        result = service._handle_ytmusic_error(error, "test")
        
        assert isinstance(result, ExternalServiceError)

    def test_handle_error_with_none_ytmusic(self):
        """Test error handling when YTMusic client is None."""
        service = BaseService(None)
        error = Exception("Test error")
        
        result = service._handle_ytmusic_error(error, "test")
        
        assert isinstance(result, ExternalServiceError)

    def test_exception_to_dict(self, mock_ytmusic):
        """Test that exceptions can be converted to dict for JSON response."""
        service = BaseService(mock_ytmusic)
        error = Exception("Rate limit exceeded 429")
        
        result = service._handle_ytmusic_error(error, "test")
        error_dict = result.to_dict()
        
        assert error_dict["error"] is True
        assert error_dict["error_code"] == "RATE_LIMIT_ERROR"
        assert "message" in error_dict
        assert "details" in error_dict


class TestBaseServiceErrorScenarios:
    """Test error scenarios for BaseService."""

    def test_multiple_error_patterns_in_message(self, mock_ytmusic):
        """Test error message containing multiple patterns."""
        service = BaseService(mock_ytmusic)
        # Message with both rate limit and JSON patterns
        # Rate limit is checked first in lowercase, so it matches
        error = Exception("Rate limit exceeded and JSON error")
        
        result = service._handle_ytmusic_error(error, "test")
        
        # Rate limit is detected because "rate limit" is checked in lowercase
        assert isinstance(result, RateLimitError)

    def test_rate_limit_case_insensitive(self, mock_ytmusic):
        """Test that rate limit detection is case insensitive."""
        service = BaseService(mock_ytmusic)
        
        error1 = Exception("RATE LIMIT EXCEEDED")
        result1 = service._handle_ytmusic_error(error1, "test")
        assert isinstance(result1, RateLimitError)
        
        error2 = Exception("Rate Limit")
        result2 = service._handle_ytmusic_error(error2, "test")
        assert isinstance(result2, RateLimitError)

    def test_not_found_case_insensitive(self, mock_ytmusic):
        """Test that not found detection is case insensitive."""
        service = BaseService(mock_ytmusic)
        
        error1 = Exception("NOT FOUND")
        result1 = service._handle_ytmusic_error(error1, "test")
        assert isinstance(result1, ResourceNotFoundError)
        
        error2 = Exception("Not Found")
        result2 = service._handle_ytmusic_error(error2, "test")
        assert isinstance(result2, ResourceNotFoundError)
