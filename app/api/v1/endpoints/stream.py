"""Stream endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from app.services.stream_service import StreamService
from app.core.circuit_breaker import youtube_stream_circuit

router = APIRouter()


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get("/{video_id}")
async def get_stream_url(
    video_id: str,
    service: StreamService = Depends(get_stream_service)
):
    """
    Get audio stream URL using yt-dlp.
    
    - Cached for 10 minutes to reduce YouTube API calls
    - Circuit breaker protects against rate limiting
    - Returns 429 if YouTube is rate-limited
    """
    try:
        return await service.get_stream_url(video_id)
    except Exception as e:
        error_message = str(e)
        
        # Check if it's a rate limit / circuit breaker error
        if 'rate-limit' in error_message.lower() or 'circuit breaker' in error_message.lower():
            status = youtube_stream_circuit.get_status()
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "YouTube API rate-limited",
                    "message": error_message,
                    "circuit_breaker": status,
                    "retry_after": status['remaining_time_seconds']
                }
            )
        
        raise HTTPException(status_code=500, detail=error_message)
