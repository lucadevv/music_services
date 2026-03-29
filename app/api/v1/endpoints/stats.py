"""Stats and monitoring endpoints."""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from app.schemas.stats import StatsResponse
from app.schemas.errors import COMMON_ERROR_RESPONSES
from app.api.v1.endpoints.auth import verify_admin_key

router = APIRouter(tags=["stats"])

logger = logging.getLogger(__name__)


@router.get(
    "/stats",
    response_model=StatsResponse,
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
        },
        **COMMON_ERROR_RESPONSES
    }
)
async def get_stats(
    _verified: None = Depends(verify_admin_key),
) -> StatsResponse:
    """Obtiene estadísticas completas del servicio."""
    try:
        from app.core.config import get_settings
        from app.core.cache import get_cache_stats
        from app.core.circuit_breaker import youtube_stream_circuit
        from app.core.background_cache import cache_manager
    except Exception as e:
        logger.error(f"Failed to import required modules: {e}")
        return StatsResponse(
            service="YouTube Music Service",
            error=f"Configuration not available: {str(e)}"
        )

    try:
        settings = get_settings()
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return StatsResponse(
            service="YouTube Music Service",
            error=f"Configuration not available: {str(e)}"
        )

    try:
        cache_stats = await get_cache_stats()
    except Exception as e:
        logger.warning(f"Failed to get cache stats: {e}")
        cache_stats = {"enabled": False, "error": str(e)}

    try:
        circuit_status = youtube_stream_circuit.get_status()
    except Exception as e:
        logger.warning(f"Failed to get circuit breaker status: {e}")
        circuit_status = {"state": "unknown", "error": str(e)}

    try:
        cache_metrics = cache_manager.get_metrics()
    except Exception as e:
        logger.warning(f"Failed to get cache manager metrics: {e}")
        cache_metrics = {"error": str(e)}

    return StatsResponse(
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        rate_limiting={
            "enabled": settings.RATE_LIMIT_ENABLED,
            "limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "limit_per_hour": settings.RATE_LIMIT_PER_HOUR
        },
        caching=cache_stats,
        cache_manager=cache_metrics,
        circuit_breaker={"youtube_stream": circuit_status},
        performance={
            "compression": settings.ENABLE_COMPRESSION,
            "http_timeout": settings.HTTP_TIMEOUT,
            "max_workers": settings.MAX_WORKERS
        }
    )
