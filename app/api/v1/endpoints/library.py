"""Library endpoints."""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["library"])


@router.get(
    "/",
    summary="Library information",
    description="Información sobre endpoints de biblioteca. Los endpoints de biblioteca requieren autenticación de usuario.",
    response_description="Información y endpoints públicos alternativos",
    responses={
        200: {
            "description": "Información obtenida exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Library endpoints require user authentication. Use /api/v1/explore for public content.",
                        "public_endpoints": {
                            "explore": "/api/v1/explore",
                            "charts": "/api/v1/explore/charts",
                            "moods": "/api/v1/explore/moods",
                            "search": "/api/v1/search"
                        }
                    }
                }
            }
        }
    }
)
async def library_info() -> Dict[str, Any]:
    """
    Información sobre endpoints de biblioteca.
    
    Los endpoints de biblioteca requieren autenticación de usuario para acceder a contenido personal.
    Para contenido público, usa los endpoints de `/explore`, `/search` y `/browse`.
    """
