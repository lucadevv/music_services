"""Circuit breaker for YouTube API rate limiting."""
import time
from typing import Optional, Dict, Any
from enum import Enum
from app.core.config import get_settings

settings = get_settings()


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Rate limited, blocking requests
    HALF_OPEN = "half_open"  # Testing if rate limit is cleared


class CircuitBreaker:
    """Circuit breaker to handle YouTube rate limiting."""
    
    def __init__(
        self,
        failure_threshold: int = 3,
        timeout: int = 600,  # 10 minutes
        half_open_timeout: int = 60  # 1 minute
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_timeout = half_open_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None
        self.half_open_at: Optional[float] = None
    
    def is_open(self) -> bool:
        """Check if circuit is open (rate limited)."""
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.opened_at and (time.time() - self.opened_at) >= self.timeout:
                # Move to half-open state
                self.state = CircuitState.HALF_OPEN
                self.half_open_at = time.time()
                return False
            return True
        
        if self.state == CircuitState.HALF_OPEN:
            # Check if half-open timeout passed
            if self.half_open_at and (time.time() - self.half_open_at) >= self.half_open_timeout:
                # Try closing the circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                return False
            return False
        
        return False
    
    def record_success(self):
        """Record a successful request."""
        if self.state == CircuitState.HALF_OPEN:
            # Success in half-open, close the circuit
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_at = None
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self, error_message: str = ""):
        """Record a failed request (rate limit detected)."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        # Check if error message indicates rate limiting
        is_rate_limit = any(keyword in error_message.lower() for keyword in [
            'rate-limit',
            'rate limit',
            'rate-limited',
            'too many requests',
            '429',
            'resource_exhausted'
        ])
        
        if is_rate_limit or self.failure_count >= self.failure_threshold:
            # Open the circuit
            self.state = CircuitState.OPEN
            self.opened_at = time.time()
            self.failure_count = 0  # Reset for next cycle
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        remaining_time = 0
        if self.state == CircuitState.OPEN and self.opened_at:
            remaining_time = max(0, self.timeout - (time.time() - self.opened_at))
        elif self.state == CircuitState.HALF_OPEN and self.half_open_at:
            remaining_time = max(0, self.half_open_timeout - (time.time() - self.half_open_at))
        
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "remaining_time_seconds": int(remaining_time),
            "is_blocked": self.is_open()
        }


# Global circuit breaker instance for YouTube stream API
youtube_stream_circuit = CircuitBreaker(
    failure_threshold=2,  # Open after 2 rate limit errors
    timeout=600,  # 10 minutes
    half_open_timeout=60  # 1 minute
)
