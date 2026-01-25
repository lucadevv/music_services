"""Upload endpoints."""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["uploads"])


@router.get(
    "/",
    summary="Uploads information",
    description="Información sobre endpoints de uploads. Los endpoints de uploads requieren autenticación de usuario.",
    response_description="Información y endpoints públicos alternativos",
    responses={
        200: {
            "description": "Información obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Upload endpoints require user authentication and are for managing personal uploaded content.",
                        "public_endpoints": {
                            "explore": "/api/v1/explore",
                            "charts": "/api/v1/explore/charts",
                            "moods": "/api/v1/explore/moods",
                            "search": "/api/v1/search",
                            "browse": "/api/v1/browse"
                        }
                    }
                }
            }
        }
    }
)
async def uploads_info() -> Dict[str, Any]:
    """
    Información sobre endpoints de uploads.
    
    Los endpoints de uploads requieren autenticación de usuario para gestionar contenido personal subido.
    Para contenido público, usa los endpoints de `/explore`, `/search` y `/browse`.
    """
