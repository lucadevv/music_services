"""Stats schemas for API responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class RateLimitingStats(BaseModel):
    """Rate limiting statistics."""
    
    enabled: bool = Field(..., description="Whether rate limiting is enabled")
    limit_per_minute: Optional[int] = Field(None, description="Requests allowed per minute")
    limit_per_hour: Optional[int] = Field(None, description="Requests allowed per hour")
    error: Optional[str] = Field(None, description="Error message if stats unavailable")
    
    model_config = ConfigDict(extra="allow")


class CachingStats(BaseModel):
    """Caching statistics."""
    
    enabled: Optional[bool] = Field(None, description="Whether caching is enabled")
    size: Optional[int] = Field(None, description="Current cache size")
    max_size: Optional[int] = Field(None, description="Maximum cache size")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    error: Optional[str] = Field(None, description="Error message if stats unavailable")
    
    model_config = ConfigDict(extra="allow")


class CacheManagerStats(BaseModel):
    """Cache manager metrics."""
    
    hits: Optional[int] = Field(None, description="Cache hits")
    misses: Optional[int] = Field(None, description="Cache misses")
    size: Optional[int] = Field(None, description="Current cache size")
    max_size: Optional[int] = Field(None, description="Maximum cache size")
    error: Optional[str] = Field(None, description="Error message if stats unavailable")
    
    model_config = ConfigDict(extra="allow")


class CircuitBreakerState(BaseModel):
    """Circuit breaker state for a specific service."""
    
    state: Optional[str] = Field(None, description="Circuit breaker state (OPEN, CLOSED, HALF_OPEN)")
    failure_count: Optional[int] = Field(None, description="Number of consecutive failures")
    remaining_time_seconds: Optional[int] = Field(None, description="Seconds until retry")
    error: Optional[str] = Field(None, description="Error message if stats unavailable")
    
    model_config = ConfigDict(extra="allow")


class CircuitBreakerStats(BaseModel):
    """Circuit breaker statistics."""
    
    youtube_stream: Optional[CircuitBreakerState] = Field(None, description="YouTube stream circuit breaker")
    
    model_config = ConfigDict(extra="allow")


class PerformanceStats(BaseModel):
    """Performance configuration statistics."""
    
    compression: Optional[bool] = Field(None, description="Whether compression is enabled")
    http_timeout: Optional[int] = Field(None, description="HTTP timeout in seconds")
    max_workers: Optional[int] = Field(None, description="Maximum worker threads")
    
    model_config = ConfigDict(extra="allow")


class StatsResponse(BaseModel):
    """Response for stats endpoint."""
    
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    error: Optional[str] = Field(None, description="Error message if stats unavailable")
    rate_limiting: Optional[Dict[str, Any]] = Field(None, description="Rate limiting configuration")
    caching: Optional[Dict[str, Any]] = Field(None, description="Caching statistics")
    cache_manager: Optional[Dict[str, Any]] = Field(None, description="Cache manager metrics")
    circuit_breaker: Optional[Dict[str, Any]] = Field(None, description="Circuit breaker states")
    performance: Optional[Dict[str, Any]] = Field(None, description="Performance configuration")
    
    model_config = ConfigDict(extra="allow")
