"""Unit tests for CircuitBreaker."""
import pytest
import time
from unittest.mock import patch

from app.core.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreaker:
    """Test cases for CircuitBreaker class."""

    def test_init_default_values(self):
        """Test CircuitBreaker initialization with defaults."""
        cb = CircuitBreaker()
        
        assert cb.failure_threshold == 3
        assert cb.timeout == 600
        assert cb.half_open_timeout == 60
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_init_custom_values(self):
        """Test CircuitBreaker initialization with custom values."""
        cb = CircuitBreaker(
            failure_threshold=5,
            timeout=300,
            half_open_timeout=30,
        )
        
        assert cb.failure_threshold == 5
        assert cb.timeout == 300
        assert cb.half_open_timeout == 30


class TestCircuitBreakerStates:
    """Test cases for CircuitBreaker state transitions."""

    def test_is_open_when_closed(self):
        """Test is_open returns False when circuit is closed."""
        cb = CircuitBreaker()
        
        assert cb.is_open() is False

    def test_is_open_when_open(self):
        """Test is_open returns True when circuit is open."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.opened_at = time.time()
        
        assert cb.is_open() is True

    def test_is_open_transitions_to_half_open(self):
        """Test circuit transitions to half-open after timeout."""
        cb = CircuitBreaker(timeout=0)  # Immediate timeout
        cb.state = CircuitState.OPEN
        cb.opened_at = time.time() - 1  # Set in the past
        
        assert cb.is_open() is False  # Now in half-open
        assert cb.state == CircuitState.HALF_OPEN

    def test_is_open_half_open_to_closed(self):
        """Test circuit closes after half-open timeout."""
        cb = CircuitBreaker(half_open_timeout=0)
        cb.state = CircuitState.HALF_OPEN
        cb.half_open_at = time.time() - 1  # Set in the past
        
        assert cb.is_open() is False
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestRecordSuccess:
    """Test cases for record_success method."""

    def test_record_success_in_closed_state(self):
        """Test record_success in closed state resets failure count."""
        cb = CircuitBreaker()
        cb.failure_count = 2
        
        cb.record_success()
        
        assert cb.failure_count == 0

    def test_record_success_in_half_open_closes_circuit(self):
        """Test record_success in half-open state closes circuit."""
        cb = CircuitBreaker()
        cb.state = CircuitState.HALF_OPEN
        cb.half_open_at = time.time()
        
        cb.record_success()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.half_open_at is None

    def test_record_success_in_open_state(self):
        """Test record_success in open state does nothing."""
        cb = CircuitBreaker()
        cb.state = CircuitState.OPEN
        cb.opened_at = time.time()
        
        cb.record_success()
        
        # State should remain open
        assert cb.state == CircuitState.OPEN


class TestRecordFailure:
    """Test cases for record_failure method."""

    def test_record_failure_increments_count(self):
        """Test record_failure increments failure count."""
        cb = CircuitBreaker()
        
        cb.record_failure("Some error")
        
        assert cb.failure_count == 1

    def test_record_failure_opens_on_threshold(self):
        """Test circuit opens when threshold is reached."""
        cb = CircuitBreaker(failure_threshold=2)
        
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        
        assert cb.state == CircuitState.OPEN
        assert cb.opened_at is not None

    def test_record_failure_opens_on_rate_limit(self):
        """Test circuit opens on rate limit error regardless of count."""
        cb = CircuitBreaker(failure_threshold=10)
        
        cb.record_failure("429 Rate limit exceeded")
        
        assert cb.state == CircuitState.OPEN

    def test_record_failure_detects_rate_limit_patterns(self):
        """Test record_failure detects various rate limit patterns."""
        patterns = [
            "rate-limit exceeded",
            "Rate limit hit",
            "rate-limited",
            "Too many requests",
            "429",
            "resource_exhausted",
        ]
        
        for pattern in patterns:
            cb = CircuitBreaker(failure_threshold=100)
            cb.record_failure(pattern)
            assert cb.state == CircuitState.OPEN, f"Failed for pattern: {pattern}"

    def test_record_failure_resets_count_on_open(self):
        """Test failure count resets when circuit opens."""
        cb = CircuitBreaker(failure_threshold=2)
        
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        
        # Count should be reset when circuit opens
        assert cb.failure_count == 0


class TestGetStatus:
    """Test cases for get_status method."""

    def test_get_status_closed(self):
        """Test get_status when circuit is closed."""
        cb = CircuitBreaker()
        
        status = cb.get_status()
        
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["remaining_time_seconds"] == 0
        assert status["is_blocked"] is False

    def test_get_status_open(self):
        """Test get_status when circuit is open."""
        cb = CircuitBreaker(timeout=600)
        cb.state = CircuitState.OPEN
        cb.opened_at = time.time()
        
        status = cb.get_status()
        
        assert status["state"] == "open"
        assert status["is_blocked"] is True
        assert 0 < status["remaining_time_seconds"] <= 600

    def test_get_status_half_open(self):
        """Test get_status when circuit is half-open."""
        cb = CircuitBreaker(half_open_timeout=60)
        cb.state = CircuitState.HALF_OPEN
        cb.half_open_at = time.time()
        
        status = cb.get_status()
        
        assert status["state"] == "half_open"
        assert status["is_blocked"] is False
        assert 0 < status["remaining_time_seconds"] <= 60

    def test_get_status_remaining_time(self):
        """Test remaining_time_seconds calculation."""
        cb = CircuitBreaker(timeout=100)
        cb.state = CircuitState.OPEN
        cb.opened_at = time.time() - 50  # 50 seconds ago
        
        status = cb.get_status()
        
        # Should be approximately 50 seconds remaining
        assert 40 < status["remaining_time_seconds"] <= 50


class TestCircuitBreakerIntegration:
    """Integration tests for CircuitBreaker."""

    def test_full_cycle(self):
        """Test a full circuit breaker cycle."""
        cb = CircuitBreaker(failure_threshold=2, timeout=0, half_open_timeout=0)
        
        # Initially closed
        assert cb.state == CircuitState.CLOSED
        assert cb.is_open() is False
        
        # Record failures to open
        cb.record_failure("Error 1")
        cb.record_failure("Error 2")
        assert cb.state == CircuitState.OPEN
        
        # Check is_open transitions to half-open
        assert cb.is_open() is False  # Now half-open
        assert cb.state == CircuitState.HALF_OPEN
        
        # Success closes the circuit
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_failure_in_half_open_reopens(self):
        """Test that failure in half-open reopens circuit."""
        cb = CircuitBreaker(failure_threshold=1, timeout=0)
        
        # Open the circuit
        cb.record_failure("Error")
        assert cb.state == CircuitState.OPEN
        
        # Transition to half-open
        cb.is_open()
        assert cb.state == CircuitState.HALF_OPEN
        
        # Failure in half-open reopens
        cb.record_failure("Another error")
        assert cb.state == CircuitState.OPEN
