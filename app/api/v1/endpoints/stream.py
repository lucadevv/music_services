"""Stream endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from app.services.stream_service import StreamService

router = APIRouter()


def get_stream_service() -> StreamService:
    """Dependency to get stream service."""
    return StreamService()


@router.get("/{video_id}")
async def get_stream_url(
    video_id: str,
    service: StreamService = Depends(get_stream_service)
):
    """Get audio stream URL using yt-dlp."""
    try:
        return await service.get_stream_url(video_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
