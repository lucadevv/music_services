"""Upload endpoints - Simplified (uploads require user authentication)."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def uploads_info():
    """Upload endpoints info - uploads require user authentication."""
    return {
        "message": "Upload endpoints require user authentication and are for managing personal uploaded content.",
        "public_endpoints": {
            "explore": "/api/v1/explore",
            "charts": "/api/v1/explore/charts",
            "moods": "/api/v1/explore/moods",
            "search": "/api/v1/search",
            "browse": "/api/v1/browse"
        }
    }
