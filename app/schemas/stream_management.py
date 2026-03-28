"""Stream management schemas for cache endpoints."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class CacheStatsResponse(BaseModel):
    """Response for stream cache statistics endpoint."""
    
    keys: Optional[int] = Field(None, description="Number of cached keys")
    size: Optional[str] = Field(None, description="Cache size in bytes")
    ttl: Optional[int] = Field(None, description="Default TTL in seconds")
    
    model_config = ConfigDict(extra="allow")


class CacheClearResponse(BaseModel):
    """Response for clearing all stream cache."""
    
    status: str = Field(..., description="Status of the operation")
    pattern: Optional[str] = Field(None, description="Cache pattern cleared")
    
    model_config = ConfigDict(extra="allow")


class CacheMetadataInfo(BaseModel):
    """Cache metadata information."""
    
    metadata: Optional[bool] = Field(None, description="Whether metadata is cached")
    metadata_timestamp: Optional[int] = Field(None, description="Timestamp of cached metadata")
    metadata_value: Optional[Any] = Field(None, description="Cached metadata value")
    stream_url: Optional[bool] = Field(None, description="Whether stream URL is cached")
    url_timestamp: Optional[int] = Field(None, description="Timestamp of cached URL")
    url_value: Optional[str] = Field(None, description="Cached URL value (truncated)")
    
    model_config = ConfigDict(extra="allow")


class CacheInfoResponse(BaseModel):
    """Response for cache info endpoint."""
    
    videoId: str = Field(..., description="Video ID")
    cached: Optional[CacheMetadataInfo] = Field(None, description="Cache information")
    
    model_config = ConfigDict(extra="allow")


class CacheDeleteInfo(BaseModel):
    """Information about deleted cache entries."""
    
    metadata: Optional[bool] = Field(None, description="Whether metadata was deleted")
    stream_url: Optional[bool] = Field(None, description="Whether stream URL was deleted")
    
    model_config = ConfigDict(extra="allow")


class CacheDeleteResponse(BaseModel):
    """Response for deleting cache for a specific video."""
    
    videoId: str = Field(..., description="Video ID")
    deleted: Optional[CacheDeleteInfo] = Field(None, description="Deletion result")
    
    model_config = ConfigDict(extra="allow")


class StreamCacheStatusResponse(BaseModel):
    """Response for stream cache status endpoint."""
    
    videoId: str = Field(..., description="Video ID")
    cached: bool = Field(..., description="Whether the stream URL is cached")
    expiresIn: Optional[int] = Field(None, description="TTL remaining in seconds")
    
    model_config = ConfigDict(extra="allow")
