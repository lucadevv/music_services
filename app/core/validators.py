"""Input validators for YouTube Music API parameters.

This module provides validation functions for common YouTube Music
identifiers and parameters to ensure data integrity and prevent
invalid requests from reaching the external services.
"""
import re
from typing import Optional

from app.core.exceptions import ValidationError


def validate_video_id(video_id: str) -> str:
    """Validate YouTube video ID format.
    
    YouTube video IDs are exactly 11 characters long and contain
    only alphanumeric characters, hyphens, and underscores.
    
    Args:
        video_id: The video ID to validate.
    
    Returns:
        The validated video ID (unchanged).
    
    Raises:
        ValidationError: If video_id is invalid.
    
    Examples:
        >>> validate_video_id("rMbATaj7Il8")
        'rMbATaj7Il8'
        >>> validate_video_id("short")
        ValidationError: ID de video inválido...
    """
    if not video_id:
        raise ValidationError(
            message="ID de video es requerido.",
            details={"field": "video_id", "reason": "empty_value"}
        )
    
    if len(video_id) != 11:
        raise ValidationError(
            message="ID de video inválido. Debe tener exactamente 11 caracteres.",
            details={
                "field": "video_id", 
                "reason": "invalid_length",
                "expected_length": 11,
                "actual_length": len(video_id)
            }
        )
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', video_id):
        raise ValidationError(
            message="ID de video contiene caracteres inválidos.",
            details={
                "field": "video_id", 
                "reason": "invalid_characters",
                "hint": "Solo se permiten letras, números, guiones y guiones bajos"
            }
        )
    
    return video_id


def validate_channel_id(channel_id: str) -> str:
    """Validate YouTube channel ID format.
    
    YouTube channel IDs start with 'UC' followed by 22 additional
    alphanumeric characters, hyphens, and underscores.
    
    Args:
        channel_id: The channel ID to validate.
    
    Returns:
        The validated channel ID (unchanged).
    
    Raises:
        ValidationError: If channel_id is invalid.
    
    Examples:
        >>> validate_channel_id("UCyPbsv_g9MHXLns1GrT2HQw")
        'UCyPbsv_g9MHXLns1GrT2HQw'
        >>> validate_channel_id("invalid")
        ValidationError: ID de canal inválido...
    """
    if not channel_id:
        raise ValidationError(
            message="ID de canal es requerido.",
            details={"field": "channel_id", "reason": "empty_value"}
        )
    
    if not channel_id.startswith('UC'):
        raise ValidationError(
            message="ID de canal inválido. Debe empezar con 'UC'.",
            details={
                "field": "channel_id", 
                "reason": "invalid_prefix",
                "hint": "Los IDs de canal de YouTube empiezan con 'UC'"
            }
        )
    
    if len(channel_id) != 24:
        raise ValidationError(
            message="ID de canal inválido. Debe tener 24 caracteres.",
            details={
                "field": "channel_id", 
                "reason": "invalid_length",
                "expected_length": 24,
                "actual_length": len(channel_id)
            }
        )
    
    if not re.match(r'^UC[a-zA-Z0-9_-]+$', channel_id):
        raise ValidationError(
            message="ID de canal contiene caracteres inválidos.",
            details={
                "field": "channel_id", 
                "reason": "invalid_characters"
            }
        )
    
    return channel_id


def validate_playlist_id(playlist_id: str) -> str:
    """Validate YouTube playlist ID format.
    
    YouTube playlist IDs typically start with 'PL' followed by
    additional characters (variable length).
    
    Args:
        playlist_id: The playlist ID to validate.
    
    Returns:
        The validated playlist ID (unchanged).
    
    Raises:
        ValidationError: If playlist_id is invalid.
    """
    if not playlist_id:
        raise ValidationError(
            message="ID de playlist es requerido.",
            details={"field": "playlist_id", "reason": "empty_value"}
        )
    
    if len(playlist_id) < 2:
        raise ValidationError(
            message="ID de playlist inválido. Muy corto.",
            details={
                "field": "playlist_id", 
                "reason": "too_short",
                "min_length": 2
            }
        )
    
    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', playlist_id):
        raise ValidationError(
            message="ID de playlist contiene caracteres inválidos.",
            details={
                "field": "playlist_id", 
                "reason": "invalid_characters"
            }
        )
    
    return playlist_id


def validate_browse_id(browse_id: str) -> str:
    """Validate YouTube browse ID format.
    
    Browse IDs are used for navigation and can have various prefixes
    (MPm, VL, etc.) with variable lengths.
    
    Args:
        browse_id: The browse ID to validate.
    
    Returns:
        The validated browse ID (unchanged).
    
    Raises:
        ValidationError: If browse_id is invalid.
    """
    if not browse_id:
        raise ValidationError(
            message="ID de navegación es requerido.",
            details={"field": "browse_id", "reason": "empty_value"}
        )
    
    if len(browse_id) < 2:
        raise ValidationError(
            message="ID de navegación inválido. Muy corto.",
            details={
                "field": "browse_id", 
                "reason": "too_short"
            }
        )
    
    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', browse_id):
        raise ValidationError(
            message="ID de navegación contiene caracteres inválidos.",
            details={
                "field": "browse_id", 
                "reason": "invalid_characters"
            }
        )
    
    return browse_id


def validate_search_query(query: str) -> str:
    """Validate search query string.
    
    Ensures the search query is not empty and within reasonable length.
    
    Args:
        query: The search query to validate.
    
    Returns:
        The validated and stripped query.
    
    Raises:
        ValidationError: If query is invalid.
    """
    if not query:
        raise ValidationError(
            message="Query de búsqueda es requerido.",
            details={"field": "query", "reason": "empty_value"}
        )
    
    # Strip whitespace
    query = query.strip()
    
    if not query:
        raise ValidationError(
            message="Query de búsqueda no puede estar vacío.",
            details={"field": "query", "reason": "whitespace_only"}
        )
    
    if len(query) > 200:
        raise ValidationError(
            message="Query de búsqueda muy largo. Máximo 200 caracteres.",
            details={
                "field": "query", 
                "reason": "too_long",
                "max_length": 200,
                "actual_length": len(query)
            }
        )
    
    return query


def validate_limit(limit: int, min_val: int = 1, max_val: int = 100) -> int:
    """Validate limit parameter for pagination.
    
    Args:
        limit: The limit value to validate.
        min_val: Minimum allowed value (default: 1).
        max_val: Maximum allowed value (default: 100).
    
    Returns:
        The validated limit.
    
    Raises:
        ValidationError: If limit is out of range.
    """
    if limit < min_val:
        raise ValidationError(
            message=f"El límite debe ser al menos {min_val}.",
            details={
                "field": "limit", 
                "reason": "below_minimum",
                "min_value": min_val,
                "actual_value": limit
            }
        )
    
    if limit > max_val:
        raise ValidationError(
            message=f"El límite no puede ser mayor a {max_val}.",
            details={
                "field": "limit", 
                "reason": "above_maximum",
                "max_value": max_val,
                "actual_value": limit
            }
        )
    
    return limit


def validate_search_filter(filter_value: Optional[str]) -> Optional[str]:
    """Validate search filter parameter.
    
    Args:
        filter_value: The filter value to validate (can be None).
    
    Returns:
        The validated filter value or None.
    
    Raises:
        ValidationError: If filter value is not valid.
    """
    if filter_value is None:
        return None
    
    valid_filters = {
        "songs", "videos", "albums", "artists", "playlists", 
        "community_playlists", "featured_playlists", "uploads"
    }
    
    if filter_value not in valid_filters:
        raise ValidationError(
            message=f"Filtro de búsqueda inválido.",
            details={
                "field": "filter", 
                "reason": "invalid_value",
                "valid_values": list(valid_filters),
                "actual_value": filter_value
            }
        )
    
    return filter_value


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize a string value by removing potentially dangerous content.
    
    Removes control characters and truncates to max_length.
    
    Args:
        value: The string to sanitize.
        max_length: Maximum allowed length.
    
    Returns:
        Sanitized string.
    """
    if not value:
        return value
    
    # Remove control characters except newlines and tabs
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    
    # Truncate if needed
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()
