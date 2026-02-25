"""Stream endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Path, status
from typing import Dict, Any
from app.services.stream_service import StreamService
from app.core.circuit_breaker import youtube_stream_circuit

router = APIRouter(tags=["stream"])


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get(
    "/{video_id}",
    summary="Get audio stream URL",
    description="Obtiene la URL directa de stream de audio de una canción usando yt-dlp. Incluye caché inteligente y circuit breaker.",
    response_description="URL de stream y metadatos",
    responses={
        200: {
            "description": "Stream URL obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "title": "Song Title",
                        "artist": "Artist Name",
                        "duration": 180,
                        "thumbnail": "https://i.ytimg.com/vi/.../maxresdefault.jpg",
                        "url": "https://rr5---sn-..."
                    }
                }
            }
        },
        429: {
            "description": "YouTube API rate-limited",
            "content": {
                "application/json": {
                    "example": {
                        "error": "YouTube API rate-limited",
                        "message": "Circuit breaker activado",
                        "circuit_breaker": {"state": "OPEN", "remaining_time_seconds": 300},
                        "retry_after": 300
                    }
                }
            }
        },
        500: {"description": "Error interno del servidor"}
    }
)
async def get_stream_url(
    video_id: str = Path(..., description="ID del video/canción", examples={"example1": {"value": "rMbATaj7Il8"}}),
    service: StreamService = Depends(get_stream_service)
) -> Dict[str, Any]:
    """
    Obtiene la URL directa de stream de audio de una canción.
    
    **Características:**
    - Caché inteligente: Metadatos (1 día), Stream URL (4 horas)
    - Circuit breaker: Protege contra rate limiting de YouTube
    - Formato: Mejor calidad de audio disponible (bestaudio/best)
    
    **Respuesta incluye:**
    - `url`: URL directa de stream de audio
    - `title`: Título de la canción
    - `artist`: Artista
    - `duration`: Duración en segundos
    - `thumbnail`: URL de thumbnail en mejor calidad
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
