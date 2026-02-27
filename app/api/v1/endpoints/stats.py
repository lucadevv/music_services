"""Stats and monitoring endpoints."""
from fastapi import APIRouter
from typing import Dict, Any
from app.core.cache import get_cache_stats
from app.core.config import get_settings
from app.core.circuit_breaker import youtube_stream_circuit

router = APIRouter(tags=["stats"])
settings = get_settings()


@router.get(
    "/stats",
    summary="Get service statistics",
    description="Obtiene estadísticas del servicio: rate limiting, caché, circuit breaker y rendimiento.",
    response_description="Estadísticas del servicio",
    responses={
        200: {
            "description": "Estadísticas obtenidas exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "service": "YouTube Music Service",
                        "version": "1.0.0",
                        "rate_limiting": {
                            "enabled": True,
                            "limit_per_minute": 60,
                            "limit_per_hour": 1000
                        },
                        "caching": {
                            "enabled": True,
                            "size": 150,
                            "max_size": 1000,
                            "ttl": 300
                        },
                        "circuit_breaker": {
                            "youtube_stream": {
                                "state": "CLOSED",
                                "failure_count": 0,
                                "remaining_time_seconds": 0
                            }
                        },
                        "performance": {
                            "compression": True,
                            "http_timeout": 30,
                            "max_workers": 10
                        }
                    }
                }
            }
        }
    }
)
async def get_stats() -> Dict[str, Any]:
    """Obtiene estadísticas completas del servicio."""
    cache_stats = get_cache_stats()
    circuit_status = youtube_stream_circuit.get_status()
    
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "rate_limiting": {
            "enabled": settings.RATE_LIMIT_ENABLED,
            "limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "limit_per_hour": settings.RATE_LIMIT_PER_HOUR
        },
        "caching": cache_stats,
        "circuit_breaker": {
            "youtube_stream": circuit_status
        },
        "performance": {
            "compression": settings.ENABLE_COMPRESSION,
            "http_timeout": settings.HTTP_TIMEOUT,
            "max_workers": settings.MAX_WORKERS
        }
    }
